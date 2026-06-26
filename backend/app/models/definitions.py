"""Definition entities (Architektur §5.1) — geseedete Konfiguration.

Field names follow Architektur §5.1 exactly; Folgephasen depend on them.
JSON columns use SQLAlchemy's generic ``JSON`` type (runs on SQLite + Postgres).
"""

from __future__ import annotations

from sqlalchemy import (
    JSON,
    Boolean,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import QuestionType
from app.models.mixins import UUIDPrimaryKey


class ProcessDefinition(UUIDPrimaryKey, Base):
    __tablename__ = "process_definitions"

    key: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    modules: Mapped[list["ModuleDefinition"]] = relationship(
        back_populates="process", cascade="all, delete-orphan"
    )


class ModuleDefinition(UUIDPrimaryKey, Base):
    __tablename__ = "module_definitions"

    key: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    process_def_id: Mapped[str] = mapped_column(
        ForeignKey("process_definitions.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    short_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    # intro: {goal, why, who, effort, explainer}
    intro: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    responsible_role: Mapped[str | None] = mapped_column(String(128), nullable=True)
    estimated_effort: Mapped[str | None] = mapped_column(String(128), nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # unlock_rule: {"type":"always"} | {"type":"after","requires":[...]} | {"type":"manual"}
    unlock_rule: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    ai_knowledge_config: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    output_schema_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    target_mappings: Mapped[list | None] = mapped_column(JSON, nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    process: Mapped["ProcessDefinition"] = relationship(back_populates="modules")
    steps: Mapped[list["StepDefinition"]] = relationship(
        back_populates="module", cascade="all, delete-orphan"
    )
    # TemplateDefinition is linked by (scope, owner_key) rather than an FK
    # (owner may be a module key or a step key); resolved via query in later phases.


class StepDefinition(UUIDPrimaryKey, Base):
    __tablename__ = "step_definitions"

    key: Mapped[str] = mapped_column(String(128), nullable=False)
    module_def_id: Mapped[str] = mapped_column(
        ForeignKey("module_definitions.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ai_knowledge_config: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    module: Mapped["ModuleDefinition"] = relationship(back_populates="steps")
    questions: Mapped[list["QuestionDefinition"]] = relationship(
        back_populates="step", cascade="all, delete-orphan"
    )


class QuestionDefinition(UUIDPrimaryKey, Base):
    __tablename__ = "question_definitions"

    key: Mapped[str] = mapped_column(String(128), nullable=False)
    step_def_id: Mapped[str] = mapped_column(
        ForeignKey("step_definitions.id"), nullable=False
    )
    label: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    type: Mapped[QuestionType] = mapped_column(
        String(32), nullable=False
    )
    required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    options: Mapped[list | None] = mapped_column(JSON, nullable=True)
    help_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_help_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    validation_rules: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    knowledge_scope: Mapped[list | None] = mapped_column(JSON, nullable=True)
    # visibility_rule: {"questionKey":"...","equals":"..."} | null (always visible)
    visibility_rule: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    step: Mapped["StepDefinition"] = relationship(back_populates="questions")


class TemplateDefinition(UUIDPrimaryKey, Base):
    __tablename__ = "template_definitions"

    key: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    scope: Mapped[str] = mapped_column(String(16), nullable=False)  # module | step
    owner_key: Mapped[str] = mapped_column(String(128), nullable=False)
    type: Mapped[str] = mapped_column(String(16), nullable=False)  # email | file | text
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[str | None] = mapped_column(String(255), nullable=True)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    file_type: Mapped[str | None] = mapped_column(String(32), nullable=True)


class KnowledgeEntry(UUIDPrimaryKey, Base):
    __tablename__ = "knowledge_entries"

    key: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str | None] = mapped_column(String(128), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)


class User(UUIDPrimaryKey, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
