from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from secrets import token_urlsafe
from uuid import uuid4

@dataclass
class AwarenessRun:
    run_id: str
    run_token: str
    age_band: str
    household_type: str
    answers: dict[str,str] = field(default_factory=dict)
    completed: bool = False
    handoff_token: str | None = None
    claimed_by: str | None = None
    claimed_at: datetime | None = None
    expires_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc)+timedelta(hours=4))

class MemoryStore:
    """Development/test store only. Production must use PostgreSQL."""
    def __init__(self):
        self.runs: dict[str, AwarenessRun] = {}
        self.member_run: dict[str, str] = {}

    def create_run(self, age_band: str, household_type: str) -> AwarenessRun:
        run = AwarenessRun(
            run_id=f"AWR_{uuid4()}",
            run_token=token_urlsafe(24),
            age_band=age_band,
            household_type=household_type,
        )
        self.runs[run.run_id] = run
        return run

    def get_run(self, run_id: str) -> AwarenessRun | None:
        return self.runs.get(run_id)

    def get_run_by_handoff(self, handoff_token: str) -> AwarenessRun | None:
        return next((r for r in self.runs.values() if r.handoff_token == handoff_token), None)

    def claim_handoff(self, handoff_token: str, subject: str) -> tuple[AwarenessRun | None, bool]:
        run = self.get_run_by_handoff(handoff_token)
        if not run:
            return None, False
        if run.claimed_by:
            return run, run.claimed_by == subject
        run.claimed_by = subject
        run.claimed_at = datetime.now(timezone.utc)
        self.member_run[subject] = run.run_id
        return run, False

    def get_member_run(self, subject: str) -> AwarenessRun | None:
        run_id = self.member_run.get(subject)
        return self.runs.get(run_id) if run_id else None

store = MemoryStore()
