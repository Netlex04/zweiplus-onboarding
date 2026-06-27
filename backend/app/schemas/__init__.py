"""Pydantic v2 request/response schemas (mirrors docs/openapi.yaml).

Response models serialise with camelCase aliases to match the OpenAPI contract;
populated by Python attribute name internally.
"""

from app.schemas.auth import LoginRequest, LoginResponse
from app.schemas.common import CamelModel, ErrorResponse
from app.schemas.definitions import (
    ModuleDefinitionSummary,
    ProcessDefinitionOut,
)
from app.schemas.files import FileUploadOut
from app.schemas.module import ModuleDetail, ModuleIntro, ModuleStepSummary
from app.schemas.process import (
    CreateProcessRequest,
    Dashboard,
    ModuleCard,
    ProcessSummary,
)
from app.schemas.step import (
    AnswerInput,
    AnswerOut,
    BackendValidationResultOut,
    PutAnswersRequest,
    PutAnswersResponse,
    QuestionOut,
    StepDetail,
    ValidationError,
    ValidationWarning,
)
from app.schemas.template import TemplateOut

__all__ = [
    "CamelModel",
    "ErrorResponse",
    "LoginRequest",
    "LoginResponse",
    "ProcessDefinitionOut",
    "ModuleDefinitionSummary",
    "CreateProcessRequest",
    "Dashboard",
    "ModuleCard",
    "ProcessSummary",
    "ModuleDetail",
    "ModuleIntro",
    "ModuleStepSummary",
    "AnswerInput",
    "AnswerOut",
    "BackendValidationResultOut",
    "PutAnswersRequest",
    "PutAnswersResponse",
    "QuestionOut",
    "StepDetail",
    "ValidationError",
    "ValidationWarning",
    "FileUploadOut",
    "TemplateOut",
]
