"""Idempotent seed loader (Annahme A8/A9).

Reads JSON seeds from ``backend/seeds/`` and upserts them into the database by
natural key. Running it twice produces no duplicates and updates existing rows
in place. Designed to be safe to call on every startup.

Usage:
    python -m app.seeds.loader            # load against the configured DATABASE_URL

Seeds:
    seeds/process.json            -> ProcessDefinition
    seeds/modules/*.json          -> ModuleDefinition + StepDefinition
                                     + QuestionDefinition + TemplateDefinition
    seeds/knowledge.json          -> KnowledgeEntry
    seeds/users.json              -> User (passwords hashed)
"""

from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import BACKEND_DIR
from app.db.session import session_scope
from app.models import (
    KnowledgeEntry,
    ModuleDefinition,
    ProcessDefinition,
    QuestionDefinition,
    StepDefinition,
    TemplateDefinition,
    User,
)
from app.security import hash_password

SEEDS_DIR = BACKEND_DIR / "seeds"


def _load_json(path: Path) -> object:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def _set_attrs(obj: object, values: dict) -> None:
    for attr, value in values.items():
        setattr(obj, attr, value)


def _upsert_by_key(
    session: Session, model: type, key: str, values: dict
) -> tuple[object, bool]:
    """Insert or update a row identified by its unique ``key`` column.

    Returns (instance, created).
    """
    instance = session.scalar(select(model).where(model.key == key))
    created = instance is None
    if instance is None:
        instance = model(key=key, **values)
        session.add(instance)
    else:
        _set_attrs(instance, values)
    return instance, created


def _seed_process(session: Session) -> ProcessDefinition:
    data = _load_json(SEEDS_DIR / "process.json")
    process, _ = _upsert_by_key(
        session,
        ProcessDefinition,
        data["key"],
        {"name": data["name"], "description": data.get("description")},
    )
    session.flush()
    return process


def _seed_knowledge(session: Session) -> int:
    entries = _load_json(SEEDS_DIR / "knowledge.json")
    for entry in entries:
        _upsert_by_key(
            session,
            KnowledgeEntry,
            entry["key"],
            {
                "title": entry["title"],
                "category": entry.get("category"),
                "content": entry["content"],
            },
        )
    return len(entries)


def _seed_users(session: Session) -> int:
    users = _load_json(SEEDS_DIR / "users.json")
    for user in users:
        email = user["email"]
        existing = session.scalar(select(User).where(User.email == email))
        values = {
            "name": user.get("name"),
            "role": user["role"],
            "password_hash": hash_password(user["password"]),
        }
        if existing is None:
            session.add(User(email=email, **values))
        else:
            # Keep role/name in sync; only re-hash if no hash present (avoid churn).
            existing.name = values["name"]
            existing.role = values["role"]
            if not existing.password_hash:
                existing.password_hash = values["password_hash"]
    return len(users)


def _seed_module(session: Session, process_id: str, data: dict) -> None:
    module, _ = _upsert_by_key(
        session,
        ModuleDefinition,
        data["key"],
        {
            "process_def_id": process_id,
            "name": data["name"],
            "short_description": data.get("short_description"),
            "intro": data.get("intro"),
            "responsible_role": data.get("responsible_role"),
            "estimated_effort": data.get("estimated_effort"),
            "order_index": data.get("order_index", 0),
            "unlock_rule": data.get("unlock_rule"),
            "ai_knowledge_config": data.get("ai_knowledge_config"),
            "output_schema_key": data.get("output_schema_key"),
            "target_mappings": data.get("target_mappings"),
            "enabled": data.get("enabled", True),
        },
    )
    session.flush()

    for step_data in data.get("steps", []):
        _seed_step(session, module, step_data)


def _seed_step(session: Session, module: ModuleDefinition, data: dict) -> None:
    # Step keys are unique per module; existing step is matched on (module, key).
    step = session.scalar(
        select(StepDefinition).where(
            StepDefinition.module_def_id == module.id,
            StepDefinition.key == data["key"],
        )
    )
    values = {
        "module_def_id": module.id,
        "title": data["title"],
        "description": data.get("description"),
        "order_index": data.get("order_index", 0),
        "ai_knowledge_config": data.get("ai_knowledge_config"),
    }
    if step is None:
        step = StepDefinition(key=data["key"], **values)
        session.add(step)
    else:
        _set_attrs(step, values)
    session.flush()

    for question_data in data.get("questions", []):
        _seed_question(session, step, question_data)

    for template_data in data.get("templates", []):
        _seed_template(session, scope="step", owner_key=data["key"], data=template_data)


def _seed_question(
    session: Session, step: StepDefinition, data: dict
) -> None:
    question = session.scalar(
        select(QuestionDefinition).where(
            QuestionDefinition.step_def_id == step.id,
            QuestionDefinition.key == data["key"],
        )
    )
    values = {
        "step_def_id": step.id,
        "label": data["label"],
        "description": data.get("description"),
        "type": data["type"],
        "required": data.get("required", False),
        "options": data.get("options"),
        "help_text": data.get("help_text"),
        "ai_help_enabled": data.get("ai_help_enabled", False),
        "validation_rules": data.get("validation_rules"),
        "knowledge_scope": data.get("knowledge_scope"),
        "visibility_rule": data.get("visibility_rule"),
        "order_index": data.get("order_index", 0),
    }
    if question is None:
        question = QuestionDefinition(key=data["key"], **values)
        session.add(question)
    else:
        _set_attrs(question, values)


def _seed_template(
    session: Session, scope: str, owner_key: str, data: dict
) -> None:
    _upsert_by_key(
        session,
        TemplateDefinition,
        data["key"],
        {
            "scope": scope,
            "owner_key": owner_key,
            "type": data["type"],
            "title": data["title"],
            "subject": data.get("subject"),
            "body": data.get("body"),
            "file_name": data.get("file_name"),
            "file_type": data.get("file_type"),
        },
    )


def _seed_modules(session: Session, process_id: str) -> int:
    modules_dir = SEEDS_DIR / "modules"
    files = sorted(modules_dir.glob("*.json"))
    for path in files:
        _seed_module(session, process_id, _load_json(path))
    return len(files)


def load_seeds(session: Session | None = None) -> dict[str, int]:
    """Load all seeds idempotently.

    If ``session`` is provided, the caller manages the transaction; otherwise a
    transactional scope is opened and committed.
    """

    def _run(s: Session) -> dict[str, int]:
        process = _seed_process(s)
        counts = {
            "process_definitions": 1,
            "module_definitions": _seed_modules(s, process.id),
            "knowledge_entries": _seed_knowledge(s),
            "users": _seed_users(s),
        }
        return counts

    if session is not None:
        return _run(session)
    with session_scope() as scoped:
        return _run(scoped)


def main() -> None:
    counts = load_seeds()
    print("Seeds loaded (idempotent):")
    for name, count in counts.items():
        print(f"  {name}: {count}")


if __name__ == "__main__":
    main()
