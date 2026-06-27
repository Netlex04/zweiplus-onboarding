"""E2E smoke: login -> process -> module -> step -> answers -> validate ->
complete -> progress rises -> follow-up module becomes available."""

from tests.conftest import login


def _module(dash, key):
    return next(m for m in dash["modules"] if m["key"] == key)


def test_full_customer_flow(api):
    client, _ = api
    auth = login(client, "kunde@demo.test")
    h = auth["headers"]

    # Create process
    dash = client.post(
        "/api/processes",
        headers=h,
        json={
            "processDefKey": "datenschutz_basis_onboarding",
            "customerName": "Demo Kunde",
        },
    ).json()
    pid = dash["processInstanceId"]
    assert dash["overallProgress"] == 0
    assert _module(dash, "software_inventory")["locked"] is False
    assert _module(dash, "tom_erfassung")["locked"] is True
    assert _module(dash, "avv_onboarding")["locked"] is True

    # Open software_inventory module + its steps
    sw_mid = _module(dash, "software_inventory")["moduleInstanceId"]
    module_detail = client.get(f"/api/modules/{sw_mid}", headers=h).json()
    steps = {s["key"]: s["stepInstanceId"] for s in module_detail["steps"]}

    # --- Step 1: basic_information ---
    basic_id = steps["basic_information"]
    step = client.get(f"/api/steps/{basic_id}", headers=h).json()
    assert any(q["key"] == "used_software" for q in step["questions"])

    # Invalid first (missing required) -> validation fails
    bad = client.put(
        f"/api/steps/{basic_id}/answers",
        headers=h,
        json={"answers": [{"questionKey": "additional_notes", "value": "x"}]},
    ).json()
    assert bad["validation"]["passed"] is False

    # Now valid
    ok = client.put(
        f"/api/steps/{basic_id}/answers",
        headers=h,
        json={"answers": [{"questionKey": "used_software", "value": ["DATEV"]}]},
    ).json()
    assert ok["validation"]["passed"] is True

    comp = client.post(f"/api/steps/{basic_id}/complete", headers=h)
    assert comp.status_code == 200
    assert comp.json()["status"] == "complete"

    # --- Step 2: data_transfer (visibility) ---
    dt_id = steps["data_transfer"]
    # third_country = ja -> details becomes visible
    client.put(
        f"/api/steps/{dt_id}/answers",
        headers=h,
        json={"answers": [{"questionKey": "third_country", "value": "ja"}]},
    )
    dt = client.get(f"/api/steps/{dt_id}", headers=h).json()
    details = next(q for q in dt["questions"] if q["key"] == "third_country_details")
    assert details["visible"] is True

    # answer details, complete
    client.put(
        f"/api/steps/{dt_id}/answers",
        headers=h,
        json={
            "answers": [
                {"questionKey": "third_country", "value": "ja"},
                {"questionKey": "third_country_details", "value": "USA, SCC"},
            ]
        },
    )
    comp2 = client.post(f"/api/steps/{dt_id}/complete", headers=h)
    assert comp2.status_code == 200

    # --- Progress rose + follow-up unlocked ---
    dash2 = client.get(f"/api/processes/{pid}", headers=h).json()
    sw_card = _module(dash2, "software_inventory")
    assert sw_card["progress"] == 100
    assert dash2["overallProgress"] > 0
    assert _module(dash2, "tom_erfassung")["locked"] is False
    assert _module(dash2, "avv_onboarding")["locked"] is False


def test_complete_gate_returns_409(api):
    client, _ = api
    auth = login(client, "kunde@demo.test")
    h = auth["headers"]
    dash = client.post(
        "/api/processes",
        headers=h,
        json={
            "processDefKey": "datenschutz_basis_onboarding",
            "customerName": "Demo Kunde",
        },
    ).json()
    sw_mid = _module(dash, "software_inventory")["moduleInstanceId"]
    detail = client.get(f"/api/modules/{sw_mid}", headers=h).json()
    basic_id = next(
        s["stepInstanceId"] for s in detail["steps"] if s["key"] == "basic_information"
    )
    # Complete without answers -> 409
    resp = client.post(f"/api/steps/{basic_id}/complete", headers=h)
    assert resp.status_code == 409
    assert resp.json()["error"] == "conflict"
