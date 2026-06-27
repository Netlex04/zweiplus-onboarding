"""Auth + role-based access at the HTTP layer."""

from tests.conftest import login


def test_login_success_and_role(api):
    client, _ = api
    resp = client.post(
        "/api/auth/login", json={"email": "kunde@demo.test", "password": "demo1234"}
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["role"] == "customer"
    assert body["token"]


def test_login_bad_password(api):
    client, _ = api
    resp = client.post(
        "/api/auth/login", json={"email": "kunde@demo.test", "password": "wrong"}
    )
    assert resp.status_code == 401
    assert resp.json()["error"] == "unauthorized"


def test_protected_requires_token(api):
    client, _ = api
    assert client.get("/api/process-definitions").status_code == 401


def test_list_processes_requires_staff_role(api):
    client, _ = api
    customer = login(client, "kunde@demo.test")
    reviewer = login(client, "review@zweiplus.test")

    assert client.get("/api/processes", headers=customer["headers"]).status_code == 403
    assert client.get("/api/processes", headers=reviewer["headers"]).status_code == 200


def test_customer_cannot_access_other_process(api):
    client, _ = api
    reviewer = login(client, "review@zweiplus.test")
    # Reviewer creates a process for a *different* customer name.
    created = client.post(
        "/api/processes",
        headers=reviewer["headers"],
        json={
            "processDefKey": "datenschutz_basis_onboarding",
            "customerName": "Andere Firma",
        },
    ).json()
    pid = created["processInstanceId"]

    customer = login(client, "kunde@demo.test")  # name "Demo Kunde"
    resp = client.get(f"/api/processes/{pid}", headers=customer["headers"])
    assert resp.status_code == 403


def test_customer_can_access_own_process(api):
    client, _ = api
    reviewer = login(client, "review@zweiplus.test")
    created = client.post(
        "/api/processes",
        headers=reviewer["headers"],
        json={
            "processDefKey": "datenschutz_basis_onboarding",
            "customerName": "Demo Kunde",
        },
    ).json()
    pid = created["processInstanceId"]

    customer = login(client, "kunde@demo.test")
    resp = client.get(f"/api/processes/{pid}", headers=customer["headers"])
    assert resp.status_code == 200
