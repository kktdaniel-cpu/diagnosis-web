"""Two-member API integration checks using memory storage, not live Supabase."""
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.auth import get_current_subject
from app.main import app

ACTION = "ACT_CONFIRM_RETIREMENT_AGE"


def data(response):
    assert response.status_code == 200
    return response.json()["data"]


def claim(client, subject):
    app.dependency_overrides[get_current_subject] = lambda: subject
    run = data(client.post("/v1/awareness/runs", json={
        "age_band": "50_55", "household_type": "single"}))
    headers = {"X-Awareness-Token": run["run_token"]}
    for question in data(client.get("/v1/awareness/questions"))["questions"]:
        data(client.put(f"/v1/awareness/runs/{run['run_id']}/answers/{question['id']}",
                        headers=headers, json={"response": "UNKNOWN_OR_NOT_PREPARED"}))
    done = data(client.post(f"/v1/awareness/runs/{run['run_id']}/complete", headers=headers))
    data(client.post("/v1/me/awareness/claim", json={"handoff_token": done["handoff_token"]}))
    return done["handoff_token"]


@pytest.fixture
def two_members():
    with TestClient(app) as client:
        a, b = str(uuid4()), str(uuid4())
        token = claim(client, a)
        aid = data(client.post(f"/v1/me/actions/{ACTION}/start"))["action_instance_id"]
        data(client.post(f"/v1/me/actions/{ACTION}/{aid}/complete",
                         json={"fields": {"retirement_age": 63}}))
        facts = data(client.get("/v1/me/facts"))
        dashboard = data(client.get("/v1/me/dashboard"))
        claim(client, b)
        try:
            yield client, a, aid, token, facts, dashboard
        finally:
            app.dependency_overrides.clear()


def test_member_reads_and_coach_do_not_expose_other_members_facts(two_members):
    client, _, _, _, _, _ = two_members
    assert data(client.get("/v1/me/facts")) == {}
    dashboard = data(client.get("/v1/me/dashboard"))
    assert dashboard["confirmed_awareness_count"] == 0
    assert dashboard["recent_changes"] == []
    for endpoint in ("action-explain", "action-help"):
        payload = {"action_catalog_id": ACTION}
        if endpoint == "action-help":
            payload["question"] = "퇴직 나이를 알려주세요"
        assert data(client.post(f"/v1/me/ai/{endpoint}", json=payload))["fact_refs"] == []


def test_claim_token_cannot_be_reused_by_another_member(two_members):
    client, _, _, token, _, _ = two_members
    response = client.post("/v1/me/awareness/claim", json={"handoff_token": token})
    assert response.status_code == 409
    assert data(client.get("/v1/me/facts")) == {}


def test_foreign_mutation_and_summary_leave_owner_records_unchanged(two_members):
    client, owner, aid, _, facts, dashboard = two_members
    requests = [
        (f"/v1/me/actions/{aid}/submit", {"fields": {"retirement_age": 58}}),
        (f"/v1/me/actions/{aid}/wait", None),
        (f"/v1/me/actions/{ACTION}/{aid}/complete", {"fields": {"retirement_age": 58}}),
        ("/v1/me/ai/change-summary", {"action_instance_id": aid}),
    ]
    for path, payload in requests:
        assert client.post(path, json=payload).status_code == 404
    app.dependency_overrides[get_current_subject] = lambda: owner
    assert data(client.get("/v1/me/facts")) == facts
    assert data(client.get("/v1/me/dashboard")) == dashboard
