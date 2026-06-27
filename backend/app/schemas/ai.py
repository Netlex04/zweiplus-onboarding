"""AI endpoint request/response schemas (mirrors docs/openapi.yaml /api/ai/*).

All response models serialise with camelCase aliases (via ``CamelModel``).
"""

from __future__ import annotations

from typing import Any, Literal

from app.schemas.common import CamelModel

AiContext = Literal["dashboard", "module", "step", "question"]


class ChatMessage(CamelModel):
    role: Literal["user", "assistant"]
    content: str


class AiChatRequest(CamelModel):
    context: AiContext
    context_ref: str | None = None
    message: str
    history: list[ChatMessage] = []


class AiChatResponse(CamelModel):
    reply: str


class AiSuggestRequest(CamelModel):
    step_instance_id: str | None = None
    question_key: str | None = None


class AiSuggestionOut(CamelModel):
    """Mirrors the OpenAPI ``AiSuggestion`` schema."""

    id: str
    suggestion_type: str | None = None
    module_id: str | None = None
    step_id: str | None = None
    question_id: str | None = None
    proposed_value: Any = None
    confidence: float | None = None
    requires_review: bool = True
    open_questions: list[str] = []
    source_upload_id: str | None = None


class AiValidateRequest(CamelModel):
    step_instance_id: str


class AiValidationCheck(CamelModel):
    question: str | None = None
    ok: bool
    note: str | None = None


class AiValidationResultOut(CamelModel):
    """Mirrors the OpenAPI ``AiValidationResult`` schema."""

    id: str
    passed: bool
    checks: list[AiValidationCheck] = []
    issues: list[str] = []


class AnalyzeDocumentRequest(CamelModel):
    upload_id: str
