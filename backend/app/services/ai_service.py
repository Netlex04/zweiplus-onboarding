"""AI orchestration service (Architektur §8, FR-AI-001…007, FR-DOC-003/004).

Glues prompt composition (:mod:`app.services.ai_context`), the AI provider seam
(:mod:`app.providers.ai`) and persistence (``AiSuggestion`` / ``AiValidationResult``)
together. Structured KI output is validated against a Pydantic schema **before**
persistence and never written directly into answers or target systems
(``requires_review`` is always ``True`` — FR-AI-007).
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, ValidationError
from sqlalchemy.orm import Session

from app.models import (
    AiSuggestion,
    AiValidationResult,
    FileUpload,
    ModuleDefinition,
    ModuleInstance,
    QuestionDefinition,
    StepDefinition,
    StepInstance,
)
from app.providers.ai import AiProvider
from app.providers.storage import FileStorage
from app.services.ai_context import (
    build_system_prompt,
    gather_answer_context,
)
from app.services.module_engine import question_def_by_step


# --- Schemas the KI output is validated against before persistence (FR-AI-007) ---


class SuggestionSchema(BaseModel):
    suggestion_type: str = Field(alias="suggestionType")
    proposed_value: Any = Field(default=None, alias="proposedValue")
    confidence: float = Field(default=0.5)
    requires_review: bool = Field(default=True, alias="requiresReview")
    open_questions: list[str] = Field(default_factory=list, alias="openQuestions")

    model_config = {"populate_by_name": True}


class ValidationCheckSchema(BaseModel):
    question: str | None = None
    ok: bool
    note: str | None = None


class ValidationSchema(BaseModel):
    passed: bool
    checks: list[ValidationCheckSchema] = Field(default_factory=list)
    issues: list[str] = Field(default_factory=list)


class AiServiceError(Exception):
    """Raised when KI output is unusable (e.g. fails schema validation)."""


# --- Context resolution helpers -------------------------------------------------


def _module_def_for_step(session: Session, step: StepInstance) -> ModuleDefinition | None:
    module = session.get(ModuleInstance, step.module_instance_id)
    if module is None:
        return None
    return session.get(ModuleDefinition, module.module_def_id)


# --- Chat ----------------------------------------------------------------------


def run_chat(
    session: Session,
    provider: AiProvider,
    *,
    context: str,
    context_ref: str | None,
    message: str,
    history: list[dict],
) -> str:
    """Free-form contextual chat. Resolves knowledge by context; no persistence."""
    module_def: ModuleDefinition | None = None
    step_def: StepDefinition | None = None
    answer_summary = ""

    if context == "module" and context_ref:
        module = session.get(ModuleInstance, context_ref)
        if module is not None:
            module_def = session.get(ModuleDefinition, module.module_def_id)
            answer_summary = gather_answer_context(session, module=module)
    elif context in ("step", "question") and context_ref:
        step = session.get(StepInstance, context_ref)
        if step is not None:
            step_def = session.get(StepDefinition, step.step_def_id)
            module_def = _module_def_for_step(session, step)
            answer_summary = gather_answer_context(session, step=step)

    system = build_system_prompt(
        session, context=context, module=module_def, step=step_def
    )
    if answer_summary:
        system = f"{system}\n\n{answer_summary}"

    messages = [
        {"role": m.get("role", "user"), "content": m.get("content", "")}
        for m in history
    ]
    messages.append({"role": "user", "content": message})
    return provider.chat(system, messages)


# --- Suggest -------------------------------------------------------------------


def run_suggest(
    session: Session,
    provider: AiProvider,
    *,
    step_instance_id: str | None,
    question_key: str | None,
) -> AiSuggestion:
    """Produce a structured suggestion and persist it as an ``AiSuggestion``."""
    step: StepInstance | None = None
    step_def: StepDefinition | None = None
    module_def: ModuleDefinition | None = None
    question: QuestionDefinition | None = None
    context = "step"

    if step_instance_id:
        step = session.get(StepInstance, step_instance_id)
        if step is None:
            raise AiServiceError("Step-Instanz nicht gefunden")
        step_def = session.get(StepDefinition, step.step_def_id)
        module_def = _module_def_for_step(session, step)
        if question_key:
            context = "question"
            for q in question_def_by_step(session, step.step_def_id):
                if q.key == question_key:
                    question = q
                    break

    system = build_system_prompt(
        session,
        context=context,
        module=module_def,
        step=step_def,
        question=question,
    )
    answer_summary = (
        gather_answer_context(session, step=step) if step is not None else ""
    )
    target = (
        f"die Frage „{question.label}“" if question is not None else "diesen Step"
    )
    prompt = (
        f"Erstelle einen konkreten Antwortvorschlag für {target}. "
        f"{answer_summary}"
    )

    raw = provider.structured(system, prompt, SuggestionSchema)
    try:
        parsed = SuggestionSchema.model_validate(raw)
    except ValidationError as exc:
        raise AiServiceError(f"KI-Vorschlag ungültig: {exc}") from exc

    suggestion = AiSuggestion(
        context=context,
        module_instance_id=step.module_instance_id if step is not None else None,
        step_instance_id=step.id if step is not None else None,
        question_def_id=question.id if question is not None else None,
        suggestion_type=parsed.suggestion_type,
        payload={"proposedValue": parsed.proposed_value},
        confidence=parsed.confidence,
        requires_review=True,  # FR-AI-007: KI schreibt nie final.
        open_questions=parsed.open_questions,
    )
    session.add(suggestion)
    session.flush()
    return suggestion


# --- Validate ------------------------------------------------------------------


def run_validate(
    session: Session,
    provider: AiProvider,
    *,
    step_instance_id: str,
) -> AiValidationResult:
    """Run a semantic check over a step and persist an ``AiValidationResult``."""
    step = session.get(StepInstance, step_instance_id)
    if step is None:
        raise AiServiceError("Step-Instanz nicht gefunden")

    step_def = session.get(StepDefinition, step.step_def_id)
    module_def = _module_def_for_step(session, step)
    system = build_system_prompt(
        session, context="step", module=module_def, step=step_def
    )
    answer_summary = gather_answer_context(session, step=step)
    prompt = (
        "Prüfe die Antworten dieses Steps semantisch auf Plausibilität, "
        "Vollständigkeit, Widersprüche, zu allgemeine Angaben und "
        "Normalisierbarkeit. "
        f"{answer_summary}"
    )

    raw = provider.structured(system, prompt, ValidationSchema)
    try:
        parsed = ValidationSchema.model_validate(raw)
    except ValidationError as exc:
        raise AiServiceError(f"KI-Prüfung ungültig: {exc}") from exc

    result = AiValidationResult(
        step_instance_id=step.id,
        passed=parsed.passed,
        checks=[c.model_dump() for c in parsed.checks],
        issues=parsed.issues,
    )
    session.add(result)
    session.flush()
    return result


# --- Analyze document ----------------------------------------------------------


def run_analyze_document(
    session: Session,
    provider: AiProvider,
    storage: FileStorage,
    *,
    upload_id: str,
) -> AiSuggestion:
    """Load a file via the storage seam, extract hints, persist an ``AiSuggestion``
    with ``source_upload_id`` (provenance, FR-DOC-004)."""
    upload = session.get(FileUpload, upload_id)
    if upload is None:
        raise AiServiceError("Upload nicht gefunden")

    excerpt = ""
    try:
        data = storage.load(upload.storage_path)
        # MVP: best-effort text extraction; we do not ship a heavy parser.
        excerpt = data.decode("utf-8", errors="ignore")[:4000]
    except FileNotFoundError:
        excerpt = ""

    step = session.get(StepInstance, upload.step_instance_id)
    module_def = _module_def_for_step(session, step) if step is not None else None
    step_def = (
        session.get(StepDefinition, step.step_def_id) if step is not None else None
    )
    system = build_system_prompt(
        session, context="step", module=module_def, step=step_def
    )
    prompt = (
        "Werte den folgenden Dokumentauszug aus und leite einen "
        f"Antwortvorschlag ab (Dateiname: {upload.original_name}).\n\n"
        f"Auszug:\n{excerpt or '(kein Textinhalt extrahierbar)'}"
    )

    raw = provider.structured(system, prompt, SuggestionSchema)
    try:
        parsed = SuggestionSchema.model_validate(raw)
    except ValidationError as exc:
        raise AiServiceError(f"KI-Dokumentauswertung ungültig: {exc}") from exc

    suggestion = AiSuggestion(
        context="step" if step is not None else "module",
        module_instance_id=step.module_instance_id if step is not None else None,
        step_instance_id=upload.step_instance_id,
        question_def_id=upload.question_def_id,
        suggestion_type=parsed.suggestion_type,
        payload={"proposedValue": parsed.proposed_value},
        confidence=parsed.confidence,
        requires_review=True,
        open_questions=parsed.open_questions,
        source_upload_id=upload.id,
    )
    session.add(suggestion)
    session.flush()
    return suggestion
