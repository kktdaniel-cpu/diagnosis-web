from fastapi.testclient import TestClient
from app.main import app
from app import auth, config

client = TestClient(app)

class FakeResponse:
    status_code = 200
    def json(self):
        return {"id": "00000000-0000-0000-0000-000000000123"}

class FakeClient:
    async def __aenter__(self):
        return self
    async def __aexit__(self, exc_type, exc, tb):
        return False
    async def get(self, url, headers):
        assert url.endswith("/auth/v1/user")
        assert headers["Authorization"] == "Bearer good-token"
        return FakeResponse()

class ExpiredResponse:
    status_code = 401
    def json(self):
        return {"message":"JWT expired"}

class ExpiredClient:
    async def __aenter__(self):
        return self
    async def __aexit__(self, exc_type, exc, tb):
        return False
    async def get(self, url, headers):
        assert url.endswith("/auth/v1/user")
        return ExpiredResponse()

def test_me_requires_bearer(monkeypatch):
    monkeypatch.setattr(config, "SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setattr(config, "SUPABASE_ANON_KEY", "anon")
    r = client.get("/v1/me")
    assert r.status_code == 401

def test_member_dashboard_requires_bearer(monkeypatch):
    monkeypatch.setattr(config, "SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setattr(config, "SUPABASE_ANON_KEY", "anon")
    r = client.get("/v1/me/dashboard")
    assert r.status_code == 401

def test_expired_session_is_rejected(monkeypatch):
    monkeypatch.setattr(config, "SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setattr(config, "SUPABASE_ANON_KEY", "anon")
    monkeypatch.setattr(auth.httpx, "AsyncClient", lambda timeout: ExpiredClient())
    r = client.get("/v1/me", headers={"Authorization":"Bearer expired-token"})
    assert r.status_code == 401

def test_me_accepts_verified_supabase_user(monkeypatch):
    monkeypatch.setattr(config, "SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setattr(config, "SUPABASE_ANON_KEY", "anon")
    monkeypatch.setattr(auth.httpx, "AsyncClient", lambda timeout: FakeClient())
    r = client.get("/v1/me", headers={"Authorization":"Bearer good-token"})
    assert r.status_code == 200
    assert r.json()["data"]["authenticated"] is True


def test_precision_entry_keeps_existing_engine_separate():
    app.dependency_overrides[auth.get_current_subject]=lambda:"precision-user"
    try:
        r=client.get("/v1/me/precision/entry")
        assert r.status_code==200
        data=r.json()["data"]
        assert data["url"].startswith("https://diag.lpp20.com")
        assert data["handoff"]=="NONE"
        assert data["engine_authority"]=="diagnosis-api Ver32.42"
    finally:
        app.dependency_overrides.clear()


def test_delete_me_removes_memory_member_data():
    from app.auth import get_current_subject
    from app.catalog import QUESTIONS
    from app.store import store

    created=client.post("/v1/awareness/runs",json={"age_band":"50_55","household_type":"single"}).json()["data"]
    headers={"X-Awareness-Token":created["run_token"]}
    for q in QUESTIONS:
        assert client.put(
            f"/v1/awareness/runs/{created['run_id']}/answers/{q['id']}",
            json={"response":"UNKNOWN_OR_NOT_PREPARED"},
            headers=headers,
        ).status_code==200
    done=client.post(f"/v1/awareness/runs/{created['run_id']}/complete",headers=headers).json()["data"]

    app.dependency_overrides[get_current_subject]=lambda:"delete-user"
    try:
        assert client.post("/v1/me/awareness/claim",json={"handoff_token":done["handoff_token"]}).status_code==200
        deleted=client.delete("/v1/me")
        assert deleted.status_code==200
        assert deleted.json()["data"]["deleted"] is True
        assert "delete-user" not in store.member_run
        assert client.get("/v1/me/dashboard").json()["data"]["top3"]==[]
    finally:
        app.dependency_overrides.clear()
