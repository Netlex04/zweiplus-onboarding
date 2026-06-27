"""Review + import/canonical schemas (mirrors docs/openapi.yaml).

All response models serialise with camelCase aliases (via ``CamelModel``).
Phase 6 (Frontend Review-Screen) consumes these exact field names.
"""

from __future__ import annotations

from typing import Any

from app.models.enums import ImportStatus, ModuleStatus, ReviewStatus
from app.schemas.ai import AiSuggestionOut, AiValidationResultOut
from app.schemas.common import CamelModel
from app.schemas.step import AnswerOut, BackendValidationResultOut

# --- Review ---------------------------------------------------------------


class ReviewTaskOut(CamelModel):
    """Mirrors the OpenAPI ``ReviewTask`` schema (+ id/status fields)."""

    id: str
    module_instance_id: str
    customer_name: str | None = None
    module_name: str
    status: ReviewStatus
    notes: str | None = None


class ReviewQuestion(CamelModel):
    key: str
    label: str
    answer: AnswerOut | None = None
    ai_suggestions: list[AiSuggestionOut] = []


class ReviewStep(CamelModel):
    step_instance_id: str
    title: str
    questions: list[ReviewQuestion] = []
    ai_validation: AiValidationResultOut | None = None
    backend_validation: BackendValidationResultOut | None = None


class ReviewView(CamelModel):
    module_instance_id: str
    module_name: str
    module_status: ModuleStatus
    customer_name: str | None = None
    review_status: ReviewStatus | None = None
    steps: list[ReviewStep] = []


class PatchAnswerRequest(CamelModel):
    value: Any = None


class RequestChangesRequest(CamelModel):
    notes: str | None = None


# --- Canonical + Import ---------------------------------------------------


class CanonicalOutputOut(CamelModel):
    """Mirrors the OpenAPI ``CanonicalOutput`` schema."""

    module_instance_id: str
    schema_key: str
    data: dict[str, Any] = {}


class ImportPreviewOut(CamelModel):
    """Mirrors the OpenAPI ``ImportPreview`` schema."""

    target_system: str
    mapped_objects: list[dict[str, Any]] = []
    unmapped_fields: list[str] = []
    warnings: list[str] = []
    errors: list[str] = []


class CreateImportJobRequest(CamelModel):
    module_instance_id: str
    target_system: str = "dpms_v1"


class ImportPreviewRequest(CamelModel):
    target_system: str = "dpms_v1"


class ImportJobOut(CamelModel):
    """Mirrors the OpenAPI ``ImportJob`` schema."""

    id: str
    module_instance_id: str
    target_system: str
    status: ImportStatus
    preview: ImportPreviewOut | None = None
    errors: list[str] = []
