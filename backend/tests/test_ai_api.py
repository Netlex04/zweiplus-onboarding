"""HTTP-layer tests for /api/ai/* against the deterministic StubChatModel."""

from __future__ import annotations

import pytest

from app.api.ai import provider_dependency
from app.providers.ai import get_ai_provider
from app.providers.ai_stub import StubChatModel
from tests.conftest import login


@pytest.fixture
def ai_client(api):
    """The seeded API client with the AI provider overridden to the stub."""
    client, TestSession = api
    client.app.dependency_overrides[provider_dependency] = lambda: get_ai_provider(
        chat_model=StubChatModel()
    )
    return client, TestSession


def _create_process_and_steps(client, headers):
    created = client.post(
        "/api/processes",
        headers=headers,
        json={
            "processDefKey": "datenschutz_basis_onboarding",
            "customerName": "Demo Kunde",
        },
    ).json()
    pid = created["processInstanceId"]
    dash = client.get(f"/api/processes/{pid}", headers=headers).json()
    sw = next(m for m in dash["modules"] if m["key"] == "software_inventory")
    detail = client.get(
        f"/api/modules/{sw['moduleInstanceId']}", headers=headers
    ).json()
    steps = {s["key"]: s["stepInstanceId"] for s in detail["steps"]}
    return sw["moduleInstanceId"], steps


def test_chat_requires_auth(ai_client):
    client, _ = ai_client
    resp = client.post(
        "/api/ai/chat", json={"context": "dashboard", "message": "Hallo"}
    )
    assert resp.status_code == 401


def test_chat_dashboard_returns_reply(ai_client):
    client, _ = ai_client
    auth = login(client, "kunde@demo.test")
    resp = client.post(
        "/api/ai/chat",
        headers=auth["headers"],
        json={"context": "dashboard", "message": "Was muss ich tun?", "history": []},
    )
    assert resp.status_code == 200
    assert resp.json()["reply"]


def test_suggest_persists_ai_suggestion(ai_client):
    client, TestSession = ai_client
    auth = login(client, "kunde@demo.test")
    _, steps = _create_process_and_steps(client, auth["headers"])

    resp = client.post(
        "/api/ai/suggest",
        headers=auth["headers"],
        json={
            "stepInstanceId": steps["basic_information"],
            "questionKey": "used_software",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["requiresReview"] is True
    assert body["suggestionType"]
    assert body["proposedValue"] is not None
    assert body["stepId"] == steps["basic_information"]

    # Persisted with correct context/refs.
    from app.models import AiSuggestion, QuestionDefinition, StepInstance

    session = TestSession()
    try:
        stored = session.query(AiSuggestion).all()
        assert len(stored) == 1
        s = stored[0]
        assert s.context == "question"
        assert s.step_instance_id == steps["basic_information"]
        assert s.requires_review is True
        # question_def_id resolves to the used_software question.
        step = session.get(StepInstance, steps["basic_information"])
        q = (
            session.query(QuestionDefinition)
            .filter_by(step_def_id=step.step_def_id, key="used_software")
            .one()
        )
        assert s.question_def_id == q.id
    finally:
        session.close()


def test_validate_persists_validation_result(ai_client):
    client, TestSession = ai_client
    auth = login(client, "kunde@demo.test")
    _, steps = _create_process_and_steps(client, auth["headers"])

    resp = client.post(
        "/api/ai/validate",
        headers=auth["headers"],
        json={"stepInstanceId": steps["basic_information"]},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "passed" in body
    assert isinstance(body["checks"], list)
    assert isinstance(body["issues"], list)

    from app.models import AiValidationResult

    session = TestSession()
    try:
        stored = session.query(AiValidationResult).all()
        assert len(stored) == 1
        assert stored[0].step_instance_id == steps["basic_information"]
        assert isinstance(stored[0].checks, list)
    finally:
        session.close()


def test_analyze_document_sets_source_upload_id(ai_client):
    client, TestSession = ai_client
    auth = login(client, "kunde@demo.test")
    _, steps = _create_process_and_steps(client, auth["headers"])

    upload = client.post(
        "/api/uploads",
        headers=auth["headers"],
        data={
            "stepInstanceId": steps["basic_information"],
            "questionKey": "software_contract_upload",
        },
        files={"file": ("contract.pdf", b"%PDF-1.4 Vertrag DATEV", "application/pdf")},
    ).json()

    resp = client.post(
        "/api/ai/analyze-document",
        headers=auth["headers"],
        json={"uploadId": upload["id"]},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["sourceUploadId"] == upload["id"]
    assert body["requiresReview"] is True

    from app.models import AiSuggestion

    session = TestSession()
    try:
        stored = session.query(AiSuggestion).one()
        assert stored.source_upload_id == upload["id"]
    finally:
        session.close()


def test_prompt_never_contains_password_hash(ai_client, monkeypatch):
    """Data minimisation: the prompt handed to the LLM carries no secrets."""
    client, _ = ai_client
    auth = login(client, "kunde@demo.test")
    _, steps = _create_process_and_steps(client, auth["headers"])

    captured: list[str] = []

    from app.providers import ai_stub

    original = ai_stub.StubChatModel._respond

    def _spy(self, messages):
        for m in messages:
            captured.append(str(m.content))
        return original(self, messages)

    monkeypatch.setattr(ai_stub.StubChatModel, "_respond", _spy)

    client.post(
        "/api/ai/suggest",
        headers=auth["headers"],
        json={
            "stepInstanceId": steps["basic_information"],
            "questionKey": "used_software",
        },
    )
    blob = "\n".join(captured)
    assert blob  # the spy actually captured prompt text
    assert "password" not in blob.lower()
    assert "hash" not in blob.lower()
