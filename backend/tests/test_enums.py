"""Enums are complete and carry the exact string values (Architektur §5.3)."""

from app.models.enums import (
    AnswerSource,
    ImportStatus,
    ModuleStatus,
    QuestionType,
    ReviewStatus,
    Role,
    StepStatus,
)


def test_module_status_values():
    assert {s.value for s in ModuleStatus} == {
        "locked",
        "available",
        "not_started",
        "in_progress",
        "waiting_customer",
        "waiting_zweiplus",
        "ai_check_pending",
        "backend_validation_failed",
        "completed",
        "import_ready",
        "imported",
    }


def test_step_status_values():
    assert {s.value for s in StepStatus} == {
        "not_started",
        "in_progress",
        "incomplete",
        "ai_check_pending",
        "backend_validation_failed",
        "complete",
        "review_pending",
        "completed",
    }


def test_import_status_values():
    assert {s.value for s in ImportStatus} == {
        "not_prepared",
        "mapping_ready",
        "validated",
        "approved",
        "importing",
        "imported",
        "import_failed",
        "reimport_required",
    }


def test_question_type_values():
    assert {q.value for q in QuestionType} == {
        "single_select",
        "multi_select",
        "text",
        "file_upload",
    }


def test_role_values():
    assert {r.value for r in Role} == {"customer", "reviewer", "admin"}


def test_answer_source_values():
    assert {a.value for a in AnswerSource} == {"user", "ai", "document", "manual"}


def test_review_status_values():
    assert {r.value for r in ReviewStatus} == {
        "open",
        "in_review",
        "changes_requested",
        "approved",
    }


def test_enums_are_str():
    # str-subclassing keeps DB storage and JSON serialisation readable.
    assert ModuleStatus.LOCKED == "locked"
    assert QuestionType.TEXT == "text"
