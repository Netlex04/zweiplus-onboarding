"""Upload whitelist + template rendering at the HTTP layer."""

from tests.conftest import login


def _create_process_and_get_step(client, headers):
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
    basic = next(s for s in detail["steps"] if s["key"] == "basic_information")
    return basic["stepInstanceId"]


def test_upload_rejects_bad_type(api):
    client, _ = api
    auth = login(client, "kunde@demo.test")
    step_id = _create_process_and_get_step(client, auth["headers"])

    resp = client.post(
        "/api/uploads",
        headers=auth["headers"],
        data={"stepInstanceId": step_id, "questionKey": "software_contract_upload"},
        files={"file": ("evil.exe", b"MZ\x00", "application/octet-stream")},
    )
    assert resp.status_code == 415
    assert resp.json()["error"] == "unsupported_media_type"


def test_upload_and_download_pdf(api):
    client, _ = api
    auth = login(client, "kunde@demo.test")
    step_id = _create_process_and_get_step(client, auth["headers"])

    resp = client.post(
        "/api/uploads",
        headers=auth["headers"],
        data={"stepInstanceId": step_id, "questionKey": "software_contract_upload"},
        files={"file": ("contract.pdf", b"%PDF-1.4 hello", "application/pdf")},
    )
    assert resp.status_code == 201
    upload = resp.json()
    assert upload["originalName"] == "contract.pdf"
    assert upload["sizeBytes"] > 0

    dl = client.get(
        f"/api/uploads/{upload['id']}/download", headers=auth["headers"]
    )
    assert dl.status_code == 200
    assert dl.content == b"%PDF-1.4 hello"


def test_template_rendering(api):
    client, _ = api
    auth = login(client, "kunde@demo.test")
    created = client.post(
        "/api/processes",
        headers=auth["headers"],
        json={
            "processDefKey": "datenschutz_basis_onboarding",
            "customerName": "Demo Kunde",
        },
    ).json()
    pid = created["processInstanceId"]
    dash = client.get(f"/api/processes/{pid}", headers=auth["headers"]).json()
    sw = next(m for m in dash["modules"] if m["key"] == "software_inventory")

    resp = client.get(
        "/api/templates/software_vendor_email",
        params={"moduleInstanceId": sw["moduleInstanceId"]},
        headers=auth["headers"],
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["type"] == "email"
    assert body["subject"]


def test_template_file_download(api):
    client, _ = api
    auth = login(client, "kunde@demo.test")
    resp = client.get(
        "/api/templates/software_vendor_questionnaire/file", headers=auth["headers"]
    )
    assert resp.status_code == 200
    assert "attachment" in resp.headers["content-disposition"]
    assert len(resp.content) > 0
