"""Backend validation service (FR-VAL-001/002) — deterministic & binding.

Validates the answers of a step against its question definitions:

Technical checks:
- required fields present (only for *visible* questions per visibility_rule)
- value type matches the QuestionType
- single/multi_select values are within the question's ``options``
- file_upload references an existing FileUpload row

Domain checks (from ``validation_rules`` when present):
- ``minSelected`` — minimum number of selections for multi_select
- ``allowedFileTypes`` — accepted extensions for file_upload (defence in depth;
  the upload endpoint also enforces the global whitelist)

The result is returned as a structured ``ValidationOutcome`` and persisted as a
``BackendValidationResult`` row by ``run_step_validation``.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Answer,
    BackendValidationResult,
    FileUpload,
    QuestionDefinition,
    StepDefinition,
    StepInstance,
)
from app.models.enums import QuestionType
from app.services.module_engine import is_question_visible


@dataclass
class ValidationOutcome:
    passed: bool
    errors: list[dict] = field(default_factory=list)
    warnings: list[dict] = field(default_factory=list)


def _error(question_key: str, code: str, message: str) -> dict:
    return {"questionKey": question_key, "code": code, "message": message}


def _warning(question_key: str, message: str) -> dict:
    return {"questionKey": question_key, "message": message}


def _is_empty(value: object) -> bool:
    if value is None:
        return True
    if isinstance(value, (str, list, dict)) and len(value) == 0:
        return True
    return False


def _type_ok(question: QuestionDefinition, value: object) -> bool:
    qtype = question.type
    if qtype == QuestionType.TEXT.value:
        return isinstance(value, str)
    if qtype == QuestionType.SINGLE_SELECT.value:
        return isinstance(value, str)
    if qtype == QuestionType.MULTI_SELECT.value:
        return isinstance(value, list) and all(isinstance(v, str) for v in value)
    if qtype == QuestionType.FILE_UPLOAD.value:
        # value is the FileUpload id (string) or null
        return value is None or isinstance(value, str)
    return False


def validate_step(
    session: Session,
    step_instance: StepInstance,
) -> ValidationOutcome:
    """Run all backend checks for a step instance; return a ValidationOutcome."""
    step_def = session.get(StepDefinition, step_instance.step_def_id)
    questions = list(
        session.scalars(
            select(QuestionDefinition)
            .where(QuestionDefinition.step_def_id == step_def.id)
            .order_by(QuestionDefinition.order_index)
        )
    )
    qid_to_q = {q.id: q for q in questions}

    # Current answers keyed by question key (for visibility) and by id.
    answers_by_key: dict[str, object] = {}
    answers_by_qid: dict[str, Answer] = {}
    for ans in step_instance.answers:
        q = qid_to_q.get(ans.question_def_id)
        if q is not None:
            answers_by_key[q.key] = ans.value
            answers_by_qid[ans.question_def_id] = ans

    errors: list[dict] = []
    warnings: list[dict] = []

    for question in questions:
        visible = is_question_visible(question, answers_by_key)
        if not visible:
            continue  # hidden questions are not validated (FR-Q-007)

        ans = answers_by_qid.get(question.id)
        value = ans.value if ans is not None else None
        rules = question.validation_rules or {}

        # Required (only visible)
        if question.required and _is_empty(value):
            errors.append(
                _error(question.key, "required", "Pflichtfeld nicht ausgefüllt.")
            )
            continue

        if _is_empty(value):
            continue  # optional & empty -> nothing more to check

        # Type
        if not _type_ok(question, value):
            errors.append(
                _error(
                    question.key,
                    "type",
                    f"Wert hat nicht den erwarteten Typ für {question.type}.",
                )
            )
            continue

        # Allowed values for selects
        if question.type in (
            QuestionType.SINGLE_SELECT.value,
            QuestionType.MULTI_SELECT.value,
        ):
            options = set(question.options or [])
            chosen = [value] if question.type == QuestionType.SINGLE_SELECT.value else value
            invalid = [c for c in chosen if c not in options]
            if invalid:
                errors.append(
                    _error(
                        question.key,
                        "invalid_option",
                        f"Ungültige Auswahl: {', '.join(map(str, invalid))}.",
                    )
                )

        # min selected (domain rule)
        if question.type == QuestionType.MULTI_SELECT.value:
            min_selected = rules.get("minSelected")
            if isinstance(min_selected, int) and len(value) < min_selected:
                errors.append(
                    _error(
                        question.key,
                        "min_selected",
                        f"Mindestens {min_selected} Auswahl(en) erforderlich.",
                    )
                )

        # file_upload references an existing upload
        if question.type == QuestionType.FILE_UPLOAD.value and isinstance(value, str):
            upload = session.get(FileUpload, value)
            if upload is None:
                errors.append(
                    _error(
                        question.key,
                        "missing_upload",
                        "Referenzierte Datei existiert nicht.",
                    )
                )
            else:
                allowed = rules.get("allowedFileTypes")
                if allowed:
                    ext = (upload.original_name.rsplit(".", 1)[-1] or "").lower()
                    if ext not in {a.lower() for a in allowed}:
                        errors.append(
                            _error(
                                question.key,
                                "file_type",
                                f"Dateityp .{ext} ist für diese Frage nicht erlaubt.",
                            )
                        )

    return ValidationOutcome(passed=len(errors) == 0, errors=errors, warnings=warnings)


def run_step_validation(
    session: Session, step_instance: StepInstance
) -> tuple[ValidationOutcome, BackendValidationResult]:
    """Validate and persist a ``BackendValidationResult`` row."""
    outcome = validate_step(session, step_instance)
    result = BackendValidationResult(
        step_instance_id=step_instance.id,
        passed=outcome.passed,
        errors=outcome.errors,
        warnings=outcome.warnings,
    )
    session.add(result)
    session.flush()
    return outcome, result
