from fastapi.testclient import TestClient

from app.auth import get_current_subject
from app.catalog import QUESTIONS
from app.main import app

client = TestClient(app)

def make_completed_run():
    created = client.post("/v1/awareness/runs", json={"age_band":"50_55","household_type":"couple"}).json()["data"]
    headers={"X-Awareness-Token": created["run_token"]}
    for i, q in enumerate(QUESTIONS):
        state = "CONFIRMED" if i < 4 else "UNKNOWN_OR_NOT_PREPARED"
        r=client.put(f"/v1/awareness/runs/{created['run_id']}/answers/{q['id']}", json={"response":state}, headers=headers)
        assert r.status_code == 200
    done=client.post(f"/v1/awareness/runs/{created['run_id']}/complete",headers=headers)
    assert done.status_code == 200
    return done.json()["data"]["handoff_token"]

def test_claim_then_dashboard_is_idempotent_for_same_user():
    token=make_completed_run()
    app.dependency_overrides[get_current_subject]=lambda:"user-a"
    try:
        first=client.post("/v1/me/awareness/claim",json={"handoff_token":token})
        assert first.status_code==200
        assert first.json()["data"]["idempotent"] is False
        second=client.post("/v1/me/awareness/claim",json={"handoff_token":token})
        assert second.status_code==200
        assert second.json()["data"]["idempotent"] is True
        dash=client.get("/v1/me/dashboard")
        assert dash.status_code==200
        assert dash.json()["data"]["confirmed_awareness_count"]==4
        assert len(dash.json()["data"]["top3"])==3
    finally:
        app.dependency_overrides.clear()

def test_claim_cannot_move_to_other_user():
    token=make_completed_run()
    app.dependency_overrides[get_current_subject]=lambda:"user-owner"
    try:
        assert client.post("/v1/me/awareness/claim",json={"handoff_token":token}).status_code==200
    finally:
        app.dependency_overrides.clear()

    app.dependency_overrides[get_current_subject]=lambda:"user-other"
    try:
        denied=client.post("/v1/me/awareness/claim",json={"handoff_token":token})
        assert denied.status_code==409
        assert denied.json()["detail"]["code"]=="HANDOFF_ALREADY_CLAIMED"
    finally:
        app.dependency_overrides.clear()
