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

def test_me_requires_bearer(monkeypatch):
    monkeypatch.setattr(config, "SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setattr(config, "SUPABASE_ANON_KEY", "anon")
    r = client.get("/v1/me")
    assert r.status_code == 401

def test_me_accepts_verified_supabase_user(monkeypatch):
    monkeypatch.setattr(config, "SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setattr(config, "SUPABASE_ANON_KEY", "anon")
    monkeypatch.setattr(auth.httpx, "AsyncClient", lambda timeout: FakeClient())
    r = client.get("/v1/me", headers={"Authorization":"Bearer good-token"})
    assert r.status_code == 200
    assert r.json()["data"]["authenticated"] is True
