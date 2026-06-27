"""DTO assembly: turn ORM instances into OpenAPI response dicts.

Keeps routers thin and the mapping in one place. Returns plain dicts which the
routers validate into the Pydantic response models.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import (
    Answer,
    ModuleDefinition,
    ModuleInstance,
    ProcessInstance,
    QuestionDefinition,
    StepDefinition,
    StepInstance,
)
from app.models.enums import ModuleStatus, StepStatus
from app.services import module_engine, templates


def _next_action(status: str, locked: bool) -> str | None:
    if locked:
        return None
    mapping = {
        ModuleStatus.AVAILABLE.value: "Modul starten",
        ModuleStatus.NOT_STARTED.value: "Modul starten",
        ModuleStatus.IN_PROGRESS.value: "Bearbeitung fortsetzen",
        ModuleStatus.BACKEND_VALIDATION_FAILED.value: "Eingaben korrigieren",
        ModuleStatus.WAITING_ZWEIPLUS.value: "Wartet auf Zweiplus-Prüfung",
        ModuleStatus.COMPLETED.value: "Abgeschlossen",
    }
    return mapping.get(status)


def module_card(session: Session, module: ModuleInstance) -> dict:
    mdef = session.get(ModuleDefinition, module.module_def_id)
    locked = module.status == ModuleStatus.LOCKED.value
    intro = mdef.intro or {}
    return {
        "module_instance_id": module.id,
        "key": mdef.key,
        "name": mdef.name,
        "explainer": intro.get("explainer"),
        "status": module.status,
        "progress": module_engine.module_progress(module),
        "responsible_role": module.assigned_role or mdef.responsible_role,
        "estimated_effort": mdef.estimated_effort,
        "locked": locked,
        "unlock_hint": module_engine.unlock_hint(mdef) if locked else None,
        "next_action": _next_action(module.status, locked),
    }


def dashboard(session: Session, process: ProcessInstance) -> dict:
    modules = sorted(
        process.modules,
        key=lambda m: (
            session.get(ModuleDefinition, m.module_def_id).order_index,
            session.get(ModuleDefinition, m.module_def_id).key,
        ),
    )
    return {
        "process_instance_id": process.id,
        "customer_name": process.customer_name,
        "overall_progress": module_engine.overall_progress(process),
        "modules": [module_card(session, m) for m in modules],
    }


def module_detail(session: Session, module: ModuleInstance) -> dict:
    mdef = session.get(ModuleDefinition, module.module_def_id)
    steps = sorted(
        module.steps,
        key=lambda s: session.get(StepDefinition, s.step_def_id).order_index,
    )
    step_summaries = []
    for step in steps:
        sdef = session.get(StepDefinition, step.step_def_id)
        step_summaries.append(
            {
                "step_instance_id": step.id,
                "key": sdef.key,
                "title": sdef.title,
                "status": step.status,
            }
        )
    tmpls = templates.templates_for_module(session, mdef)
    ctx = templates.build_context(session, module.id)
    return {
        "module_instance_id": module.id,
        "key": mdef.key,
        "name": mdef.name,
        "intro": mdef.intro or {},
        "status": module.status,
        "progress": module_engine.module_progress(module),
        "steps": step_summaries,
        "templates": [templates.render_template(t, ctx) for t in tmpls],
    }


def _answer_dict(answer: Answer, question_key: str) -> dict:
    return {
        "id": answer.id,
        "question_key": question_key,
        "value": answer.value,
        "source": answer.source,
        "ai_suggested": answer.ai_suggested,
        "updated_at": answer.updated_at,
    }


def step_detail(session: Session, step: StepInstance) -> dict:
    sdef = session.get(StepDefinition, step.step_def_id)
    questions = module_engine.question_def_by_step(session, sdef.id)
    answers_by_key = module_engine.answers_by_question_key(session, step)
    answer_rows = {a.question_def_id: a for a in step.answers}

    question_dtos = []
    for q in questions:
        answer = answer_rows.get(q.id)
        question_dtos.append(
            {
                "key": q.key,
                "label": q.label,
                "description": q.description,
                "type": q.type,
                "required": q.required,
                "options": q.options,
                "help_text": q.help_text,
                "ai_help_enabled": q.ai_help_enabled,
                "visible": module_engine.is_question_visible(q, answers_by_key),
                "answer": _answer_dict(answer, q.key) if answer else None,
            }
        )

    module = session.get(ModuleInstance, step.module_instance_id)
    mdef = session.get(ModuleDefinition, module.module_def_id) if module else None
    tmpls = templates.templates_for_owner(session, "step", sdef.key)
    ctx = templates.build_context(session, step.module_instance_id)
    return {
        "step_instance_id": step.id,
        "title": sdef.title,
        "description": sdef.description,
        "status": step.status,
        "templates": [templates.render_template(t, ctx) for t in tmpls],
        "questions": question_dtos,
    }
