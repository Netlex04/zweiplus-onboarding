"""String enums (Architektur §5.3).

All enums subclass ``str`` so values are stored as readable strings in the DB
and serialise transparently in JSON / Pydantic. Folgephasen (2–6) hängen an
diesen exakten Werten.
"""

from __future__ import annotations

import enum


class ModuleStatus(str, enum.Enum):
    """ModuleInstance lifecycle (Architektur §5.3)."""

    LOCKED = "locked"
    AVAILABLE = "available"
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    WAITING_CUSTOMER = "waiting_customer"
    WAITING_ZWEIPLUS = "waiting_zweiplus"
    AI_CHECK_PENDING = "ai_check_pending"
    BACKEND_VALIDATION_FAILED = "backend_validation_failed"
    COMPLETED = "completed"
    IMPORT_READY = "import_ready"
    IMPORTED = "imported"


class StepStatus(str, enum.Enum):
    """StepInstance lifecycle (Architektur §5.3)."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    INCOMPLETE = "incomplete"
    AI_CHECK_PENDING = "ai_check_pending"
    BACKEND_VALIDATION_FAILED = "backend_validation_failed"
    COMPLETE = "complete"
    REVIEW_PENDING = "review_pending"
    COMPLETED = "completed"


class ImportStatus(str, enum.Enum):
    """ImportJob lifecycle (Architektur §5.3)."""

    NOT_PREPARED = "not_prepared"
    MAPPING_READY = "mapping_ready"
    VALIDATED = "validated"
    APPROVED = "approved"
    IMPORTING = "importing"
    IMPORTED = "imported"
    IMPORT_FAILED = "import_failed"
    REIMPORT_REQUIRED = "reimport_required"


class QuestionType(str, enum.Enum):
    """Supported answer types (Anforderungen FR-Q-002)."""

    SINGLE_SELECT = "single_select"
    MULTI_SELECT = "multi_select"
    TEXT = "text"
    FILE_UPLOAD = "file_upload"


class Role(str, enum.Enum):
    """User roles (Annahme A5)."""

    CUSTOMER = "customer"
    REVIEWER = "reviewer"
    ADMIN = "admin"


class AnswerSource(str, enum.Enum):
    """Provenance of an answer (Architektur §2 Nachvollziehbarkeit)."""

    USER = "user"
    AI = "ai"
    DOCUMENT = "document"
    MANUAL = "manual"


class ReviewStatus(str, enum.Enum):
    """ReviewTask lifecycle (Architektur §5.2)."""

    OPEN = "open"
    IN_REVIEW = "in_review"
    CHANGES_REQUESTED = "changes_requested"
    APPROVED = "approved"


# Process-level status is a free-form-ish lifecycle in §5.2; kept as a small enum
# for consistency. Not listed in §5.3 but used by ProcessInstance.status.
class ProcessStatus(str, enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"


__all__ = [
    "ModuleStatus",
    "StepStatus",
    "ImportStatus",
    "QuestionType",
    "Role",
    "AnswerSource",
    "ReviewStatus",
    "ProcessStatus",
]
