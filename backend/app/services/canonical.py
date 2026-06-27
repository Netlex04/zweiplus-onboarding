"""Canonical-Output-Service (FR-INT-001) — target-system-independent model.

Collects all *visible* answers of a *completed* module into a structured,
target-system-independent dict keyed by the module's ``output_schema_key`` and
persists it as a ``CanonicalOutput`` row (idempotent: an existing row for the
module is overwritten).

The canonical shape is intentionally generic so that any ``TargetAdapter`` can
map it without knowing about the onboarding question model:

    {
        "moduleKey": "software_inventory",
        "moduleName": "Software-Erfassung",
        "outputSchemaKey": "software_inventory_canonical_v1",
        "answers": {<questionKey>: <value>, ...},      # flat, visible only
        "fields": [                                       # ordered, with meta
            {"questionKey": ..., "label": ..., "type": ...,
             "value": ..., "source": ...},
            ...
        ],
        "steps": [
            {"key": ..., "title": ..., "questionKeys": [...]},
            ...
        ],
    }

Gate (FR-REV-003): building canonical output is only allowed once the module is
``completed`` (or further along: ``import_ready`` / ``imported``).
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    CanonicalOutput,
    ModuleDefinition,
    ModuleInstance,
    StepDefinition,
    StepInstance,
)
from app.models.enums import ModuleStatus
from app.services.module_engine import (
    answers_by_question_key,
    is_question_visible,
    question_def_by_step,
)

# Module statuses from which a canonical output may be produced (FR-REV-003).
_CANONICAL_ALLOWED = {
    ModuleStatus.COMPLETED.value,
    ModuleStatus.IMPORT_READY.value,
    ModuleStatus.IMPORTED.value,
}


class CanonicalNotAllowed(Exception):
    """Raised when canonical output is requested for a non-released module."""


def _ordered_steps(session: Session, module: ModuleInstance) -> list[StepInstance]:
    return sorted(
        module.steps,
        key=lambda s: session.get(StepDefinition, s.step_def_id).order_index,
    )


def build_canonical(
    session: Session, module_instance: ModuleInstance
) -> CanonicalOutput:
    """Assemble + persist the canonical output for a released module.

    Idempotent: re-running updates the existing ``CanonicalOutput`` row.
    Raises ``CanonicalNotAllowed`` if the module is not released yet.
    """
    if module_instance.status not in _CANONICAL_ALLOWED:
        raise CanonicalNotAllowed(
            f"Modul {module_instance.id} ist nicht freigegeben "
            f"(Status {module_instance.status})."
        )

    mdef = session.get(ModuleDefinition, module_instance.module_def_id)
    schema_key = (mdef.output_schema_key if mdef else None) or "canonical_v1"

    fields: list[dict] = []
    flat: dict[str, object] = {}
    step_summaries: list[dict] = []

    for step in _ordered_steps(session, module_instance):
        sdef = session.get(StepDefinition, step.step_def_id)
        questions = question_def_by_step(session, sdef.id)
        answers_by_key = answers_by_question_key(session, step)
        answer_rows = {a.question_def_id: a for a in step.answers}

        step_question_keys: list[str] = []
        for q in questions:
            # Only include questions that are visible given current answers.
            if not is_question_visible(q, answers_by_key):
                continue
            ans = answer_rows.get(q.id)
            if ans is None or ans.value in (None, "", [], {}):
                continue
            flat[q.key] = ans.value
            fields.append(
                {
                    "questionKey": q.key,
                    "label": q.label,
                    "type": q.type,
                    "value": ans.value,
                    "source": ans.source,
                }
            )
            step_question_keys.append(q.key)

        step_summaries.append(
            {
                "key": sdef.key,
                "title": sdef.title,
                "questionKeys": step_question_keys,
            }
        )

    data = {
        "moduleKey": mdef.key if mdef else None,
        "moduleName": mdef.name if mdef else None,
        "outputSchemaKey": schema_key,
        "answers": flat,
        "fields": fields,
        "steps": step_summaries,
    }

    existing = session.scalar(
        select(CanonicalOutput).where(
            CanonicalOutput.module_instance_id == module_instance.id
        )
    )
    if existing is None:
        existing = CanonicalOutput(
            module_instance_id=module_instance.id,
            schema_key=schema_key,
            data=data,
        )
        session.add(existing)
    else:
        existing.schema_key = schema_key
        existing.data = data
    session.flush()
    return existing
