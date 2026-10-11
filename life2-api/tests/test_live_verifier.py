"""Safety gates for the opt-in verifier. These tests never contact live services."""
import pytest

from scripts import verify_dev_member_loop as verifier


def test_missing_token_never_starts_requests(monkeypatch):
    monkeypatch.delenv("LIFE2_E2E_ACCESS_TOKEN", raising=False)
    monkeypatch.setenv("LIFE2_E2E_DISPOSABLE_ACCOUNT", "1")
    monkeypatch.setattr(verifier, "run", lambda _: pytest.fail("must not run"))
    assert verifier.main() == 2


def test_token_without_disposable_opt_in_never_starts_requests(monkeypatch):
    monkeypatch.setenv("LIFE2_E2E_ACCESS_TOKEN", "synthetic-test-token")
    monkeypatch.delenv("LIFE2_E2E_DISPOSABLE_ACCOUNT", raising=False)
    monkeypatch.setattr(verifier, "run", lambda _: pytest.fail("must not run"))
    assert verifier.main() == 2


@pytest.mark.parametrize("facts,dashboard", [
    ({"existing": {}}, {}),
    ({}, {"top3": [{}]}),
    ({}, {"in_progress": [{}]}),
    ({}, {"recent_changes": [{}]}),
    ({}, {"confirmed_awareness_count": 1}),
])
def test_existing_member_data_blocks_verification(facts, dashboard):
    with pytest.raises(verifier.VerificationError, match="Blocked"):
        verifier.require_empty_member(facts, dashboard)


@pytest.mark.parametrize("household_type", ["single", "couple"])
def test_full_twelve_action_verifier_against_local_api(monkeypatch, household_type):
    from uuid import uuid4
    from fastapi.testclient import TestClient
    from app.auth import get_current_subject
    from app.main import app

    # Only /health reads this environment variable; the imported store stays in memory.
    # This exercises the verifier, and is explicitly not live Supabase evidence.
    monkeypatch.setenv("LIFE2_STORAGE_BACKEND", "supabase")
    subject = f"local-catalog-verifier-{uuid4()}"
    app.dependency_overrides[get_current_subject] = lambda: subject
    monkeypatch.setattr(verifier.httpx, "Client", lambda **kw: TestClient(
        app, headers=kw.get("headers", {})))
    try:
        verifier.run("synthetic-local-token", household_type)
    finally:
        app.dependency_overrides.clear()


def test_verifier_checks_two_distinct_local_members(monkeypatch):
    from uuid import uuid4
    from fastapi import Request
    from fastapi.testclient import TestClient
    from app.auth import get_current_subject
    from app.main import app

    subjects = {"Bearer local-owner": str(uuid4()), "Bearer local-observer": str(uuid4())}

    def subject(request: Request):
        return subjects[request.headers["Authorization"]]

    monkeypatch.setenv("LIFE2_STORAGE_BACKEND", "supabase")
    app.dependency_overrides[get_current_subject] = subject
    monkeypatch.setattr(verifier.httpx, "Client", lambda **kw: TestClient(
        app, headers=kw.get("headers", {})))
    try:
        verifier.run("local-owner", observer_token="local-observer")
    finally:
        app.dependency_overrides.clear()
