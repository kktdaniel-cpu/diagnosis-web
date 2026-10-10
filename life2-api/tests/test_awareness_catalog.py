from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_awareness_has_exactly_12_questions():
    response = client.get("/v1/awareness/questions")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 12
    assert len(body["questions"]) == 12


def test_awareness_ids_are_unique():
    body = client.get("/v1/awareness/questions").json()
    ids = [q["id"] for q in body["questions"]]
    assert len(ids) == len(set(ids))


def test_awareness_does_not_create_numeric_fact():
    body = client.get("/v1/awareness/questions").json()
    assert body["rules"]["awareness_creates_numeric_fact"] is False
    assert body["rules"]["unknown_is_zero"] is False
