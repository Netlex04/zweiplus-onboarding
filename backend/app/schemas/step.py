"""Step detail / answers / validation schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from app.models.enums import AnswerSource, QuestionType, StepStatus
from app.schemas.common import CamelModel
from app.schemas.template import TemplateOut


class AnswerOut(CamelModel):
    id: str
    question_key: str
    value: Any = None
    source: AnswerSource
    ai_suggested: bool = False
    updated_at: datetime | None = None


class QuestionOut(CamelModel):
    key: str
    label: str
    description: str | None = None
    type: QuestionType
    required: bool
    options: list[str] | None = None
    help_text: str | None = None
    ai_help_enabled: bool = False
    visible: bool = True
    answer: AnswerOut | None = None


class StepDetail(CamelModel):
    step_instance_id: str
    title: str
    description: str | None = None
    status: StepStatus
    templates: list[TemplateOut] = []
    questions: list[QuestionOut]


class ValidationError(CamelModel):
    question_key: str | None = None
    code: str
    message: str


class ValidationWarning(CamelModel):
    question_key: str | None = None
    message: str


class BackendValidationResultOut(CamelModel):
    passed: bool
    errors: list[ValidationError] = []
    warnings: list[ValidationWarning] = []


class AnswerInput(CamelModel):
    # Accepts {"questionKey": ..., "value": ...} (camelCase via CamelModel).
    question_key: str
    value: Any = None


class PutAnswersRequest(CamelModel):
    answers: list[AnswerInput]


class PutAnswersResponse(CamelModel):
    step_status: StepStatus
    validation: BackendValidationResultOut
