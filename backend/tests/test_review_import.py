"""Phase 4 tests: review gate/view, canonical, DPMS mapping, import jobs, E2E."""

from __future__ import annotations

import pytest

from tests.conftest import login


def _module(dash, key):
    return next(m for m in dash["modules"] if m["key"] == key)


def _create_process(client, headers):
    return client.post(
        "/api/processes",
        headers=headers,
        json={
            "processDefKey": "datenschutz_basis_onboarding",
            "customerName": "Demo Kunde",
        },
    ).json()


def _complete_software_inventory(client, headers, dash):
    """Drive software_inventory to all-steps-complete -> waiting_zweiplus."""
    sw_mid = _module(dash, "software_inventory")["moduleInstanceId"]
    detail = client.get(f"/api/modules/{sw_mid}", headers=headers).json()
    steps = {s["key"]: s["stepInstanceId"] for s in detail["steps"]}

    basic_id = steps["basic_information"]
    client.put(
        f"/api/steps/{basic_id}/answers",
        headers=headers,
        json={"answers": [{"questionKey": "used_software", "value": ["DATEV", "HubSpot"]}]},
    )
    client.post(f"/api/steps/{basic_id}/complete", headers=headers)

    dt_id = steps["data_transfer"]
    client.put(
        f"/api/steps/{dt_id}/answers",
        headers=headers,
        json={
            "answers": [
                {"questionKey": "third_country", "value": "ja"},
                {"questionKey": "third_country_details", "value": "USA, SCC"},
            ]
        },
    )
    client.post(f"/api/steps/{dt_id}/complete", headers=headers)
    return sw_mid


# --- Review gate ----------------------------------------------------------


def test_customer_forbidden_on_review(api):
    client, _ = api
    cust = login(client, "kunde@demo.test")["headers"]
    dash = _create_process(client, cust)
    mid = _complete_software_inventory(client, cust, dash)

    assert client.get("/api/review/tasks", headers=cust).status_code == 403
    assert client.get(f"/api/review/modules/{mid}", headers=cust).status_code == 403
    assert (
        client.post(f"/api/review/modules/{mid}/approve", headers=cust).status_code
        == 403
    )


def test_reviewer_sees_tasks_and_view_with_provenance(api):
    client, _ = api
    cust = login(client, "kunde@demo.test")["headers"]
    rev = login(client, "review@zweiplus.test")["headers"]
    dash = _create_process(client, cust)
    mid = _complete_software_inventory(client, cust, dash)

    tasks = client.get("/api/review/tasks", headers=rev).json()
    assert any(t["moduleInstanceId"] == mid for t in tasks)
    task = next(t for t in tasks if t["moduleInstanceId"] == mid)
    assert task["status"] == "open"
    assert task["customerName"] == "Demo Kunde"

    view = client.get(f"/api/review/modules/{mid}", headers=rev).json()
    assert view["moduleStatus"] == "waiting_zweiplus"
    # answer provenance present
    all_questions = [q for s in view["steps"] for q in s["questions"]]
    answered = [q for q in all_questions if q["answer"] is not None]
    assert answered
    assert all(q["answer"]["source"] == "user" for q in answered)
    # backend validation surfaced per step
    assert any(s["backendValidation"] is not None for s in view["steps"])


# --- approve / request-changes -------------------------------------------


def test_approve_transitions_module_completed(api):
    client, _ = api
    cust = login(client, "kunde@demo.test")["headers"]
    rev = login(client, "review@zweiplus.test")["headers"]
    dash = _create_process(client, cust)
    mid = _complete_software_inventory(client, cust, dash)

    resp = client.post(f"/api/review/modules/{mid}/approve", headers=rev)
    assert resp.status_code == 200
    assert resp.json()["status"] == "completed"

    tasks = client.get("/api/review/tasks", headers=rev).json()
    assert all(t["moduleInstanceId"] != mid for t in tasks)  # approved -> closed


def test_request_changes_returns_module_and_sets_task(api):
    client, _ = api
    cust = login(client, "kunde@demo.test")["headers"]
    rev = login(client, "review@zweiplus.test")["headers"]
    dash = _create_process(client, cust)
    mid = _complete_software_inventory(client, cust, dash)

    resp = client.post(
        f"/api/review/modules/{mid}/request-changes",
        headers=rev,
        json={"notes": "Bitte Drittland präzisieren."},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "in_progress"

    tasks = client.get("/api/review/tasks", headers=rev).json()
    task = next(t for t in tasks if t["moduleInstanceId"] == mid)
    assert task["status"] == "changes_requested"
    assert task["notes"] == "Bitte Drittland präzisieren."


def test_approve_from_invalid_state_409(api):
    client, _ = api
    cust = login(client, "kunde@demo.test")["headers"]
    rev = login(client, "review@zweiplus.test")["headers"]
    dash = _create_process(client, cust)
    # software_inventory is available/in_progress, NOT waiting_zweiplus
    mid = _module(dash, "software_inventory")["moduleInstanceId"]
    resp = client.post(f"/api/review/modules/{mid}/approve", headers=rev)
    assert resp.status_code == 409


# --- PATCH answer ---------------------------------------------------------


def test_patch_answer_sets_manual_source(api):
    client, _ = api
    cust = login(client, "kunde@demo.test")["headers"]
    rev = login(client, "review@zweiplus.test")["headers"]
    dash = _create_process(client, cust)
    mid = _complete_software_inventory(client, cust, dash)

    view = client.get(f"/api/review/modules/{mid}", headers=rev).json()
    answer = next(
        q["answer"]
        for s in view["steps"]
        for q in s["questions"]
        if q["answer"] is not None and q["key"] == "used_software"
    )
    resp = client.patch(
        f"/api/review/answers/{answer['id']}",
        headers=rev,
        json={"value": ["DATEV"]},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["source"] == "manual"
    assert body["value"] == ["DATEV"]
    assert body["questionKey"] == "used_software"


# --- Canonical ------------------------------------------------------------


def test_canonical_gate_rejects_non_completed(api):
    client, _ = api
    cust = login(client, "kunde@demo.test")["headers"]
    rev = login(client, "review@zweiplus.test")["headers"]
    dash = _create_process(client, cust)
    mid = _complete_software_inventory(client, cust, dash)  # waiting_zweiplus
    resp = client.post(f"/api/modules/{mid}/canonical", headers=rev)
    assert resp.status_code == 409


def test_canonical_after_approve_and_idempotent(api):
    client, TestSession = api
    cust = login(client, "kunde@demo.test")["headers"]
    rev = login(client, "review@zweiplus.test")["headers"]
    dash = _create_process(client, cust)
    mid = _complete_software_inventory(client, cust, dash)
    client.post(f"/api/review/modules/{mid}/approve", headers=rev)

    resp = client.post(f"/api/modules/{mid}/canonical", headers=rev)
    assert resp.status_code == 200
    body = resp.json()
    assert body["schemaKey"] == "software_inventory_canonical_v1"
    assert body["data"]["answers"]["used_software"] == ["DATEV", "HubSpot"]

    # Idempotent: second call updates the same row (one CanonicalOutput).
    client.post(f"/api/modules/{mid}/canonical", headers=rev)
    from app.models import CanonicalOutput

    s = TestSession()
    try:
        rows = s.query(CanonicalOutput).filter_by(module_instance_id=mid).all()
        assert len(rows) == 1
    finally:
        s.close()


# --- DPMS mapping ---------------------------------------------------------


def test_dpms_mapping_and_preview(api):
    client, _ = api
    cust = login(client, "kunde@demo.test")["headers"]
    rev = login(client, "review@zweiplus.test")["headers"]
    dash = _create_process(client, cust)
    mid = _complete_software_inventory(client, cust, dash)
    client.post(f"/api/review/modules/{mid}/approve", headers=rev)

    preview = client.post(
        f"/api/modules/{mid}/import-preview",
        headers=rev,
        json={"targetSystem": "dpms_v1"},
    ).json()
    assert preview["targetSystem"] == "dpms_v1"
    obj_types = {o["objectType"] for o in preview["mappedObjects"]}
    assert "softwareSystem" in obj_types
    assert "processingActivity" in obj_types
    names = {o.get("name") for o in preview["mappedObjects"]}
    assert "DATEV" in names and "HubSpot" in names


def test_dpms_preview_reports_unmapped_field(api):
    client, _ = api
    cust = login(client, "kunde@demo.test")["headers"]
    rev = login(client, "review@zweiplus.test")["headers"]
    dash = _create_process(client, cust)
    sw_mid = _module(dash, "software_inventory")["moduleInstanceId"]
    detail = client.get(f"/api/modules/{sw_mid}", headers=cust).json()
    steps = {s["key"]: s["stepInstanceId"] for s in detail["steps"]}

    # Answer with the intentionally-unmapped free-text field.
    client.put(
        f"/api/steps/{steps['basic_information']}/answers",
        headers=cust,
        json={
            "answers": [
                {"questionKey": "used_software", "value": ["DATEV"]},
                {"questionKey": "additional_notes", "value": "Nur intern genutzt."},
            ]
        },
    )
    client.post(f"/api/steps/{steps['basic_information']}/complete", headers=cust)
    client.put(
        f"/api/steps/{steps['data_transfer']}/answers",
        headers=cust,
        json={"answers": [{"questionKey": "third_country", "value": "nein"}]},
    )
    client.post(f"/api/steps/{steps['data_transfer']}/complete", headers=cust)
    client.post(f"/api/review/modules/{sw_mid}/approve", headers=rev)

    preview = client.post(
        f"/api/modules/{sw_mid}/import-preview", headers=rev
    ).json()
    assert "additional_notes" in preview["unmappedFields"]
    assert preview["warnings"]  # at least one warning about the unmapped field


# --- Import jobs ----------------------------------------------------------


def test_import_job_gate_before_approval_409(api):
    client, _ = api
    cust = login(client, "kunde@demo.test")["headers"]
    rev = login(client, "review@zweiplus.test")["headers"]
    dash = _create_process(client, cust)
    mid = _complete_software_inventory(client, cust, dash)  # waiting_zweiplus
    resp = client.post(
        "/api/import-jobs",
        headers=rev,
        json={"moduleInstanceId": mid, "targetSystem": "dpms_v1"},
    )
    assert resp.status_code == 409


def test_import_job_run_reaches_imported(api):
    client, _ = api
    cust = login(client, "kunde@demo.test")["headers"]
    rev = login(client, "review@zweiplus.test")["headers"]
    dash = _create_process(client, cust)
    mid = _complete_software_inventory(client, cust, dash)
    client.post(f"/api/review/modules/{mid}/approve", headers=rev)

    created = client.post(
        "/api/import-jobs",
        headers=rev,
        json={"moduleInstanceId": mid, "targetSystem": "dpms_v1"},
    )
    assert created.status_code == 201
    job = created.json()
    assert job["status"] == "mapping_ready"
    assert job["preview"]["targetSystem"] == "dpms_v1"

    run = client.post(f"/api/import-jobs/{job['id']}/run", headers=rev).json()
    assert run["status"] == "imported"

    # Module is now imported.
    detail = client.get(f"/api/modules/{mid}", headers=rev).json()
    assert detail["status"] == "imported"


# --- E2E smoke ------------------------------------------------------------


def test_e2e_review_to_import(api):
    client, _ = api
    cust = login(client, "kunde@demo.test")["headers"]
    rev = login(client, "review@zweiplus.test")["headers"]
    dash = _create_process(client, cust)
    mid = _complete_software_inventory(client, cust, dash)

    # waiting_zweiplus -> review approve -> completed
    view = client.get(f"/api/review/modules/{mid}", headers=rev).json()
    assert view["moduleStatus"] == "waiting_zweiplus"
    assert client.post(f"/api/review/modules/{mid}/approve", headers=rev).json()[
        "status"
    ] == "completed"

    # canonical
    canon = client.post(f"/api/modules/{mid}/canonical", headers=rev).json()
    assert canon["schemaKey"] == "software_inventory_canonical_v1"

    # import-preview -> create job -> run -> imported
    client.post(f"/api/modules/{mid}/import-preview", headers=rev)
    job = client.post(
        "/api/import-jobs",
        headers=rev,
        json={"moduleInstanceId": mid, "targetSystem": "dpms_v1"},
    ).json()
    run = client.post(f"/api/import-jobs/{job['id']}/run", headers=rev).json()
    assert run["status"] == "imported"
