"""All entities can be created and their relationships resolve."""

from app.models import (
    AiSuggestion,
    AiValidationResult,
    Answer,
    BackendValidationResult,
    CanonicalOutput,
    FileUpload,
    ImportJob,
    KnowledgeEntry,
    ModuleDefinition,
    ModuleInstance,
    ProcessDefinition,
    ProcessInstance,
    QuestionDefinition,
    ReviewTask,
    StepDefinition,
    StepInstance,
    TemplateDefinition,
    User,
)
from app.models.enums import AnswerSource, ModuleStatus, QuestionType, StepStatus


def test_definition_graph_and_relationships(db_session):
    process = ProcessDefinition(key="p1", name="Prozess")
    module = ModuleDefinition(
        key="m1",
        name="Modul",
        order_index=0,
        unlock_rule={"type": "always"},
        process=process,
    )
    step = StepDefinition(key="s1", title="Step", module=module)
    question = QuestionDefinition(
        key="q1",
        label="Frage?",
        type=QuestionType.TEXT.value,
        required=True,
        options=None,
        step=step,
    )
    db_session.add(process)
    db_session.commit()

    loaded = db_session.get(ProcessDefinition, process.id)
    assert loaded.modules[0].steps[0].questions[0].key == "q1"
    assert question.id is not None  # UUID PK generated
    # ProcessDefinition carries no audit timestamps (definition entity).
    assert not hasattr(loaded, "created_at")


def test_json_columns_roundtrip(db_session):
    module = ModuleDefinition(
        key="m_json",
        name="JSON",
        ai_knowledge_config={"privacyKnowledge": ["a", "b"]},
        target_mappings=["dpms_v1"],
        intro={"goal": "g"},
        process=ProcessDefinition(key="p_json", name="P"),
    )
    db_session.add(module)
    db_session.commit()
    db_session.expire_all()
    reloaded = db_session.get(ModuleDefinition, module.id)
    assert reloaded.ai_knowledge_config["privacyKnowledge"] == ["a", "b"]
    assert reloaded.target_mappings == ["dpms_v1"]
    assert reloaded.intro["goal"] == "g"


def test_instance_graph_with_answer(db_session):
    process = ProcessDefinition(key="p2", name="P2")
    module = ModuleDefinition(key="m2", name="M2", process=process)
    step = StepDefinition(key="s2", title="S2", module=module)
    question = QuestionDefinition(
        key="q2", label="L", type=QuestionType.MULTI_SELECT.value, step=step
    )
    db_session.add(process)
    db_session.commit()

    pi = ProcessInstance(process_def_id=process.id, customer_name="Acme")
    db_session.add(pi)
    db_session.flush()
    mi = ModuleInstance(
        process_instance_id=pi.id,
        module_def_id=module.id,
        status=ModuleStatus.AVAILABLE.value,
        unlocked=True,
    )
    db_session.add(mi)
    db_session.flush()
    si = StepInstance(
        module_instance_id=mi.id,
        step_def_id=step.id,
        status=StepStatus.IN_PROGRESS.value,
    )
    db_session.add(si)
    db_session.flush()
    answer = Answer(
        step_instance_id=si.id,
        question_def_id=question.id,
        value=["Microsoft 365", "DATEV"],
        source=AnswerSource.USER.value,
    )
    db_session.add(answer)
    db_session.commit()

    db_session.expire_all()
    reloaded_pi = db_session.get(ProcessInstance, pi.id)
    answer_loaded = reloaded_pi.modules[0].steps[0].answers[0]
    assert answer_loaded.value == ["Microsoft 365", "DATEV"]
    assert answer_loaded.created_at is not None  # timestamp mixin populated


def test_remaining_instance_entities_creatable(db_session):
    process = ProcessDefinition(key="p3", name="P3")
    module = ModuleDefinition(key="m3", name="M3", process=process)
    step = StepDefinition(key="s3", title="S3", module=module)
    question = QuestionDefinition(
        key="q3", label="L", type=QuestionType.FILE_UPLOAD.value, step=step
    )
    db_session.add(process)
    db_session.commit()

    pi = ProcessInstance(process_def_id=process.id)
    db_session.add(pi)
    db_session.flush()
    mi = ModuleInstance(process_instance_id=pi.id, module_def_id=module.id)
    db_session.add(mi)
    db_session.flush()
    si = StepInstance(module_instance_id=mi.id, step_def_id=step.id)
    db_session.add(si)
    db_session.flush()

    rows = [
        FileUpload(
            question_def_id=question.id,
            step_instance_id=si.id,
            original_name="f.pdf",
            storage_path="/x/f.pdf",
            size_bytes=10,
        ),
        AiSuggestion(context="question", question_def_id=question.id, payload={"v": 1}),
        AiValidationResult(step_instance_id=si.id, passed=True, checks=[]),
        BackendValidationResult(step_instance_id=si.id, passed=False, errors=["e"]),
        ReviewTask(module_instance_id=mi.id),
        CanonicalOutput(
            module_instance_id=mi.id, schema_key="x_v1", data={"a": 1}
        ),
        ImportJob(module_instance_id=mi.id, target_system="dpms"),
    ]
    db_session.add_all(rows)
    db_session.commit()
    assert all(r.id for r in rows)


def test_user_and_knowledge_unique(db_session):
    db_session.add(
        KnowledgeEntry(key="k1", title="T", category="privacy", content="C")
    )
    db_session.add(
        User(email="a@b.test", password_hash="x", role="customer", name="A")
    )
    db_session.commit()
    assert db_session.get(User, db_session.query(User).first().id).email == "a@b.test"
