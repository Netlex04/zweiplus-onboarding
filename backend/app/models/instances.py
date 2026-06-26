"""Instance entities (Architektur §5.2) — Laufzeitzustand der Kundenbearbeitung.

Field names follow Architektur §5.2 exactly; Folgephasen depend on them.
"""

from __future__ import annotations

from sqlalchemy import (
    JSON,
    Boolean,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import (
    AnswerSource,
    ImportStatus,
    ModuleStatus,
    ProcessStatus,
    ReviewStatus,
    StepStatus,
)
from app.models.mixins import CreatedAtMixin, TimestampMixin, UUIDPrimaryKey


class ProcessInstance(UUIDPrimaryKey, CreatedAtMixin, Base):
    __tablename__ = "process_instances"

    process_def_id: Mapped[str] = mapped_column(
        ForeignKey("process_definitions.id"), nullable=False
    )
    customer_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    customer_org: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=ProcessStatus.ACTIVE.value
    )

    modules: Mapped[list["ModuleInstance"]] = relationship(
        back_populates="process_instance", cascade="all, delete-orphan"
    )


class ModuleInstance(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "module_instances"

    process_instance_id: Mapped[str] = mapped_column(
        ForeignKey("process_instances.id"), nullable=False
    )
    module_def_id: Mapped[str] = mapped_column(
        ForeignKey("module_definitions.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=ModuleStatus.LOCKED.value
    )
    unlocked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    assigned_role: Mapped[str | None] = mapped_column(String(128), nullable=True)

    process_instance: Mapped["ProcessInstance"] = relationship(back_populates="modules")
    steps: Mapped[list["StepInstance"]] = relationship(
        back_populates="module_instance", cascade="all, delete-orphan"
    )


class StepInstance(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "step_instances"

    module_instance_id: Mapped[str] = mapped_column(
        ForeignKey("module_instances.id"), nullable=False
    )
    step_def_id: Mapped[str] = mapped_column(
        ForeignKey("step_definitions.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=StepStatus.NOT_STARTED.value
    )

    module_instance: Mapped["ModuleInstance"] = relationship(back_populates="steps")
    answers: Mapped[list["Answer"]] = relationship(
        back_populates="step_instance", cascade="all, delete-orphan"
    )


class Answer(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "answers"

    step_instance_id: Mapped[str] = mapped_column(
        ForeignKey("step_instances.id"), nullable=False
    )
    question_def_id: Mapped[str] = mapped_column(
        ForeignKey("question_definitions.id"), nullable=False
    )
    value: Mapped[dict | list | str | int | float | bool | None] = mapped_column(
        JSON, nullable=True
    )
    source: Mapped[str] = mapped_column(
        String(16), nullable=False, default=AnswerSource.USER.value
    )
    ai_suggested: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)

    step_instance: Mapped["StepInstance"] = relationship(back_populates="answers")


class FileUpload(UUIDPrimaryKey, CreatedAtMixin, Base):
    __tablename__ = "file_uploads"

    question_def_id: Mapped[str] = mapped_column(
        ForeignKey("question_definitions.id"), nullable=False
    )
    step_instance_id: Mapped[str] = mapped_column(
        ForeignKey("step_instances.id"), nullable=False
    )
    answer_id: Mapped[str | None] = mapped_column(
        ForeignKey("answers.id"), nullable=True
    )
    original_name: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    storage_path: Mapped[str] = mapped_column(String(512), nullable=False)
    uploaded_by: Mapped[str | None] = mapped_column(String(255), nullable=True)


class AiSuggestion(UUIDPrimaryKey, CreatedAtMixin, Base):
    __tablename__ = "ai_suggestions"

    # context: dashboard | module | step | question
    context: Mapped[str] = mapped_column(String(32), nullable=False)
    module_instance_id: Mapped[str | None] = mapped_column(
        ForeignKey("module_instances.id"), nullable=True
    )
    step_instance_id: Mapped[str | None] = mapped_column(
        ForeignKey("step_instances.id"), nullable=True
    )
    question_def_id: Mapped[str | None] = mapped_column(
        ForeignKey("question_definitions.id"), nullable=True
    )
    suggestion_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    requires_review: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    open_questions: Mapped[list | None] = mapped_column(JSON, nullable=True)
    source_upload_id: Mapped[str | None] = mapped_column(
        ForeignKey("file_uploads.id"), nullable=True
    )


class AiValidationResult(UUIDPrimaryKey, CreatedAtMixin, Base):
    __tablename__ = "ai_validation_results"

    step_instance_id: Mapped[str] = mapped_column(
        ForeignKey("step_instances.id"), nullable=False
    )
    question_def_id: Mapped[str | None] = mapped_column(
        ForeignKey("question_definitions.id"), nullable=True
    )
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    checks: Mapped[list | None] = mapped_column(JSON, nullable=True)
    issues: Mapped[list | None] = mapped_column(JSON, nullable=True)


class BackendValidationResult(UUIDPrimaryKey, CreatedAtMixin, Base):
    __tablename__ = "backend_validation_results"

    step_instance_id: Mapped[str] = mapped_column(
        ForeignKey("step_instances.id"), nullable=False
    )
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    errors: Mapped[list | None] = mapped_column(JSON, nullable=True)
    warnings: Mapped[list | None] = mapped_column(JSON, nullable=True)


class ReviewTask(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "review_tasks"

    module_instance_id: Mapped[str] = mapped_column(
        ForeignKey("module_instances.id"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=ReviewStatus.OPEN.value
    )
    reviewer: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class CanonicalOutput(UUIDPrimaryKey, CreatedAtMixin, Base):
    __tablename__ = "canonical_outputs"

    module_instance_id: Mapped[str] = mapped_column(
        ForeignKey("module_instances.id"), nullable=False
    )
    schema_key: Mapped[str] = mapped_column(String(128), nullable=False)
    data: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class ImportJob(UUIDPrimaryKey, TimestampMixin, Base):
    __tablename__ = "import_jobs"

    module_instance_id: Mapped[str] = mapped_column(
        ForeignKey("module_instances.id"), nullable=False
    )
    target_system: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=ImportStatus.NOT_PREPARED.value
    )
    mapped_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    preview: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    errors: Mapped[list | None] = mapped_column(JSON, nullable=True)
