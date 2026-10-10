from fastapi.testclient import TestClient

from app.main import app
from app.schemas import AwarenessResponse, FactStatus


client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["service"] == "life2-api"


def test_unknown_is_not_zero_contract():
    assert FactStatus.UNKNOWN.value == "UNKNOWN"
    assert FactStatus.UNKNOWN.value != "0"


def test_awareness_unknown_is_explicit():
    assert AwarenessResponse.UNKNOWN_OR_NOT_PREPARED.value == "UNKNOWN_OR_NOT_PREPARED"
