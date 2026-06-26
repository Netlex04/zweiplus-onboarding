"""ORM models and enums.

Import everything here so ``app.db.base.Base.metadata`` is fully populated
(Alembic autogenerate + ``create_all`` rely on this single import surface).
"""

from app.models.definitions import (
    KnowledgeEntry,
    ModuleDefinition,
    ProcessDefinition,
    QuestionDefinition,
    StepDefinition,
    TemplateDefinition,
    User,
)
from app.models.enums import (
    AnswerSource,
    ImportStatus,
    ModuleStatus,
    ProcessStatus,
    QuestionType,
    ReviewStatus,
    Role,
    StepStatus,
)
from app.models.instances import (
    AiSuggestion,
    AiValidationResult,
    Answer,
    BackendValidationResult,
    CanonicalOutput,
    FileUpload,
    ImportJob,
    ModuleInstance,
    ProcessInstance,
    ReviewTask,
    StepInstance,
)

__all__ = [
    # Definitions
    "ProcessDefinition",
    "ModuleDefinition",
    "StepDefinition",
    "QuestionDefinition",
    "TemplateDefinition",
    "KnowledgeEntry",
    "User",
    # Instances
    "ProcessInstance",
    "ModuleInstance",
    "StepInstance",
    "Answer",
    "FileUpload",
    "AiSuggestion",
    "AiValidationResult",
    "BackendValidationResult",
    "ReviewTask",
    "CanonicalOutput",
    "ImportJob",
    # Enums
    "ModuleStatus",
    "StepStatus",
    "ImportStatus",
    "QuestionType",
    "Role",
    "AnswerSource",
    "ReviewStatus",
    "ProcessStatus",
]
