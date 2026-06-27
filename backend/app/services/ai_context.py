"""Prompt composition for the AI service (Architektur §8 KI-Konzept).

Two responsibilities:

- :func:`build_system_prompt` — base data-protection guideline + the cascaded
  knowledge (module -> step -> question), resolved from ``KnowledgeEntry``
  contents and deduplicated. The dashboard context carries general onboarding
  orientation only, without module knowledge.
- :func:`gather_answer_context` — a compact, **data-minimised** rendering of the
  current *visible* answers (only question/answer pairs; no internal IDs,
  password hashes or secrets are ever included — §11, FR-AI-007).
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    KnowledgeEntry,
    ModuleDefinition,
    ModuleInstance,
    QuestionDefinition,
    StepDefinition,
    StepInstance,
)
from app.services.module_engine import (
    answers_by_question_key,
    is_question_visible,
    question_def_by_step,
)

# Keys inside an ``ai_knowledge_config`` block whose values are lists of
# KnowledgeEntry keys (Annahme A8 / seed structure).
_KNOWLEDGE_GROUPS = (
    "privacyKnowledge",
    "internalKnowledge",
    "targetSystemKnowledge",
)

BASE_GUIDELINE = (
    "Du bist ein Datenschutz-Assistent für ein Onboarding-Portal. Antworte "
    "sachlich, knapp und auf Deutsch. Beachte die DSGVO und gib nur "
    "datenschutzkonforme, unverbindliche Hinweise. Du triffst keine "
    "verbindlichen Entscheidungen: Deine Vorschläge müssen stets von einem "
    "Menschen geprüft werden (requiresReview). Verarbeite ausschließlich die "
    "im Kontext bereitgestellten Informationen und keine darüber hinausgehenden "
    "personenbezogenen Daten."
)

DASHBOARD_ORIENTATION = (
    "Hilf der nutzenden Person, sich im Datenschutz-Onboarding zu orientieren: "
    "Module, Reihenfolge, Zuständigkeiten und nächste Schritte. Gehe nicht auf "
    "modulspezifisches Fachwissen ein."
)


def _config_keys(config: dict | None) -> list[str]:
    keys: list[str] = []
    if not config:
        return keys
    for group in _KNOWLEDGE_GROUPS:
        values = config.get(group) or []
        keys.extend(str(k) for k in values)
    return keys


def _resolve_knowledge(session: Session, keys: list[str]) -> list[KnowledgeEntry]:
    if not keys:
        return []
    # Deduplicate while preserving cascade order (module -> step -> question).
    seen: set[str] = set()
    ordered: list[str] = []
    for key in keys:
        if key not in seen:
            seen.add(key)
            ordered.append(key)
    entries = {
        e.key: e
        for e in session.scalars(
            select(KnowledgeEntry).where(KnowledgeEntry.key.in_(ordered))
        )
    }
    return [entries[k] for k in ordered if k in entries]


def build_system_prompt(
    session: Session,
    *,
    context: str,
    module: ModuleDefinition | None = None,
    step: StepDefinition | None = None,
    question: QuestionDefinition | None = None,
) -> str:
    """Compose the system prompt for a given AI context.

    The knowledge cascade collects keys from the module's ``ai_knowledge_config``,
    then the step's, then the question's ``knowledge_scope`` — resolved to the
    ``KnowledgeEntry`` *contents* and deduplicated.
    """
    parts: list[str] = [BASE_GUIDELINE]

    if context == "dashboard":
        parts.append(DASHBOARD_ORIENTATION)
        return "\n\n".join(parts)

    keys: list[str] = []
    if module is not None:
        keys.extend(_config_keys(module.ai_knowledge_config))
    if step is not None:
        keys.extend(_config_keys(step.ai_knowledge_config))
    if question is not None:
        keys.extend(str(k) for k in (question.knowledge_scope or []))

    entries = _resolve_knowledge(session, keys)
    if entries:
        knowledge_block = "\n\n".join(
            f"### {e.title}\n{e.content}" for e in entries
        )
        parts.append("Fachwissen (für deine Hinweise):\n\n" + knowledge_block)
    return "\n\n".join(parts)


def gather_answer_context(
    session: Session,
    *,
    step: StepInstance | None = None,
    module: ModuleInstance | None = None,
) -> str:
    """Render current *visible* answers as a compact, data-minimised summary.

    Only question label/value pairs are emitted; no internal IDs, no user/secret
    fields. Invisible (visibility-rule-hidden) questions are skipped.
    """
    steps: list[StepInstance] = []
    if step is not None:
        steps = [step]
    elif module is not None:
        steps = list(module.steps)

    lines: list[str] = []
    for step_instance in steps:
        step_def = session.get(StepDefinition, step_instance.step_def_id)
        questions = question_def_by_step(session, step_instance.step_def_id)
        answers_by_key = answers_by_question_key(session, step_instance)
        for question in questions:
            if not is_question_visible(question, answers_by_key):
                continue
            value = answers_by_key.get(question.key)
            if value in (None, "", [], {}):
                continue
            rendered = ", ".join(map(str, value)) if isinstance(value, list) else str(value)
            prefix = f"[{step_def.title}] " if step_def else ""
            lines.append(f"- {prefix}{question.label}: {rendered}")

    if not lines:
        return "Es liegen noch keine Antworten vor."
    return "Bisherige Antworten:\n" + "\n".join(lines)
