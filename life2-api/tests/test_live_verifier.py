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
