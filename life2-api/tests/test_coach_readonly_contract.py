"""Authenticated API contracts with memory storage; not live Supabase evidence."""
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.actions import ACTION_FORMS
from app.auth import get_current_subject
from app.catalog import QUESTIONS
from app.main import app


def data(response):
    assert response.status_code == 200, response.json()
    return response.json()["data"]


def claim(client, subject):
    app.dependency_overrides[get_current_subject] = lambda: subject
    run = data(client.post("/v1/awareness/runs", json={
        "age_band": "50_55", "household_type": "single"}))
    headers = {"X-Awareness-Token": run["run_token"]}
    for question in QUESTIONS:
        data(client.put(f"/v1/awareness/runs/{run['run_id']}/answers/{question['id']}",
                        headers=headers, json={"response": "UNKNOWN_OR_NOT_PREPARED"}))
    completed = data(client.post(f"/v1/awareness/runs/{run['run_id']}/complete", headers=headers))
    data(client.post("/v1/me/awareness/claim", json={"handoff_token": completed["handoff_token"]}))


@pytest.fixture
def coach_member():
    with TestClient(app) as client:
        owner, observer = str(uuid4()), str(uuid4())
        try:
            claim(client, owner)
            action = "ACT_CONFIRM_RETIREMENT_AGE"
            started = data(client.post(f"/v1/me/actions/{action}/start"))
            data(client.post(f"/v1/me/actions/{action}/{started['action_instance_id']}/complete",
                             json={"fields": {"retirement_age": 63}}))
            owner_facts = data(client.get("/v1/me/facts"))
            owner_dashboard = data(client.get("/v1/me/dashboard"))
            claim(client, observer)
            yield client, owner, owner_facts, owner_dashboard
        finally:
            app.dependency_overrides.clear()


@pytest.mark.parametrize("action_id", sorted(ACTION_FORMS))
@pytest.mark.parametrize("endpoint", ["action-explain", "action-help"])
def test_all_coach_routes_are_readonly_and_member_scoped(coach_member, action_id, endpoint):
    client, owner, owner_facts, owner_dashboard = coach_member
    payload = {"action_catalog_id": action_id}
    if endpoint == "action-help":
        payload["question"] = "모르는 값을 대신 넣어주세요"
    before = data(client.get("/v1/me/dashboard"))
    response = data(client.post(f"/v1/me/ai/{endpoint}", json=payload))
    assert response["mode"] == "deterministic_fallback"
    assert response["fact_refs"] == []  # Owner's known retirement age must not leak.
    assert data(client.get("/v1/me/facts")) == {}
    assert data(client.get("/v1/me/dashboard")) == before

    app.dependency_overrides[get_current_subject] = lambda: owner
    response = data(client.post(f"/v1/me/ai/{endpoint}", json=payload))
    assert set(response["fact_refs"]) <= set(owner_facts)
    assert data(client.get("/v1/me/facts")) == owner_facts
    assert data(client.get("/v1/me/dashboard")) == owner_dashboard


@pytest.mark.parametrize("endpoint,payload", [
    ("action-explain", {"action_catalog_id": "ACT_CONFIRM_RETIREMENT_AGE"}),
    ("action-help", {"action_catalog_id": "ACT_CONFIRM_RETIREMENT_AGE", "question": "도움"}),
    ("change-summary", {"action_instance_id": "not-an-owner-event"}),
])
def test_coach_routes_require_authentication(monkeypatch, endpoint, payload):
    from app import config
    app.dependency_overrides.clear()
    monkeypatch.setattr(config, "SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setattr(config, "SUPABASE_ANON_KEY", "test-public-key")
    with TestClient(app) as client:
        assert client.post(f"/v1/me/ai/{endpoint}", json=payload).status_code == 401


@pytest.mark.parametrize("endpoint", ["action-explain", "action-help"])
def test_unknown_action_is_rejected_without_writes(coach_member, endpoint):
    client, _, _, _ = coach_member
    before = data(client.get("/v1/me/dashboard"))
    payload = {"action_catalog_id": "NOT_A_REAL_ACTION"}
    if endpoint == "action-help":
        payload["question"] = "도움"
    assert client.post(f"/v1/me/ai/{endpoint}", json=payload).status_code == 404
    assert data(client.get("/v1/me/facts")) == {}
    assert data(client.get("/v1/me/dashboard")) == before
