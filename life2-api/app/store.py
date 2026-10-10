from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from secrets import token_urlsafe
from uuid import uuid4
import os
import httpx

from . import config

class StoreError(Exception):
    def __init__(self, code: str, status_code: int = 400):
        super().__init__(code)
        self.code = code
        self.status_code = status_code

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
    top3: list[dict] = field(default_factory=list)
    findings: list[dict] = field(default_factory=list)

class MemoryStore:
    """Development/test store only."""
    def __init__(self):
        self.runs: dict[str, AwarenessRun] = {}
        self.member_run: dict[str, str] = {}

    def create_run(self, age_band: str, household_type: str) -> dict:
        run = AwarenessRun(
            run_id=f"AWR_{uuid4()}",
            run_token=token_urlsafe(24),
            age_band=age_band,
            household_type=household_type,
        )
        self.runs[run.run_id] = run
        return {"run_id":run.run_id,"run_token":run.run_token,"expires_at":run.expires_at.isoformat()}

    def put_answer(self, run_id: str, run_token: str, question_id: str, response: str) -> dict:
        run=self.runs.get(run_id)
        if not run:
            raise StoreError("RUN_NOT_FOUND",404)
        if run.run_token != run_token:
            raise StoreError("INVALID_AWARENESS_TOKEN",403)
        if run.completed:
            raise StoreError("RUN_ALREADY_COMPLETED",409)
        if datetime.now(timezone.utc)>run.expires_at:
            raise StoreError("RUN_EXPIRED",410)
        run.answers[question_id]=response
        return {"saved":True,"answered":len(run.answers),"total":12}

    def get_run(self, run_id: str, run_token: str) -> AwarenessRun:
        run=self.runs.get(run_id)
        if not run:
            raise StoreError("RUN_NOT_FOUND",404)
        if run.run_token != run_token:
            raise StoreError("INVALID_AWARENESS_TOKEN",403)
        return run

    def finalize_run(self, run_id: str, run_token: str, top3: list[dict], findings: list[dict]) -> dict:
        run=self.get_run(run_id,run_token)
        if run.completed:
            return {"handoff_token":run.handoff_token,"top3":run.top3,"findings":run.findings,"idempotent":True}
        run.completed=True
        run.handoff_token=token_urlsafe(32)
        run.top3=top3
        run.findings=findings
        return {"handoff_token":run.handoff_token,"top3":top3,"findings":findings,"idempotent":False}

    def claim_handoff(self, handoff_token: str, subject: str) -> dict:
        run=next((r for r in self.runs.values() if r.handoff_token==handoff_token),None)
        if not run or not run.completed:
            raise StoreError("HANDOFF_NOT_FOUND",404)
        if datetime.now(timezone.utc)>run.expires_at:
            raise StoreError("HANDOFF_EXPIRED",410)
        if run.claimed_by and run.claimed_by != subject:
            raise StoreError("HANDOFF_ALREADY_CLAIMED",409)
        idempotent=run.claimed_by == subject
        if not run.claimed_by:
            run.claimed_by=subject
            run.claimed_at=datetime.now(timezone.utc)
            self.member_run[subject]=run.run_id
        return {"claimed":True,"idempotent":idempotent,"dashboard":self.dashboard(subject)}

    def dashboard(self, subject: str) -> dict:
        run_id=self.member_run.get(subject)
        run=self.runs.get(run_id) if run_id else None
        if not run:
            return {"confirmed_awareness_count":0,"awareness_total":12,"top3":[],"in_progress":[],"recent_changes":[]}
        return {
            "confirmed_awareness_count":sum(1 for v in run.answers.values() if v=="CONFIRMED"),
            "awareness_total":12,
            "top3":run.top3,
            "in_progress":[],
            "recent_changes":[]
        }

class SupabaseRPCStore:
    def __init__(self):
        self.url=config.SUPABASE_URL
        self.key=config.supabase_client_key()
        self.secret=os.getenv("LIFE2_INTERNAL_RPC_SECRET","")
        if not self.url or not self.key or not self.secret:
            raise RuntimeError("supabase storage not configured")

    def _rpc(self,name:str,payload:dict):
        try:
            r=httpx.post(
                f"{self.url}/rest/v1/rpc/{name}",
                headers={"apikey":self.key,"Content-Type":"application/json"},
                json=payload,
                timeout=8.0,
            )
        except httpx.HTTPError as e:
            raise StoreError("STORAGE_UNAVAILABLE",503) from e
        if r.status_code >= 400:
            msg=(r.json().get("message") if r.headers.get("content-type","").startswith("application/json") else r.text)
            code="STORAGE_ERROR"
            status=500
            if "expired" in str(msg).lower():
                code,status="RUN_EXPIRED",410
            elif "handoff already claimed" in str(msg).lower():
                code,status="HANDOFF_ALREADY_CLAIMED",409
            elif "handoff not found" in str(msg).lower():
                code,status="HANDOFF_NOT_FOUND",404
            elif "forbidden" in str(msg).lower():
                code,status="FORBIDDEN",403
            raise StoreError(code,status)
        return r.json()

    def create_run(self,age_band:str,household_type:str)->dict:
        return self._rpc("rpc_awareness_create",{
            "p_internal_secret":self.secret,
            "p_age_band":age_band,
            "p_household_type":household_type,
        })

    def put_answer(self,run_id:str,run_token:str,question_id:str,response:str)->dict:
        return self._rpc("rpc_awareness_put_answer",{
            "p_internal_secret":self.secret,
            "p_run_id":run_id,
            "p_run_token":run_token,
            "p_question_id":question_id,
            "p_response":response,
        })

    def get_run(self,run_id:str,run_token:str):
        data=self._rpc("rpc_awareness_get",{
            "p_internal_secret":self.secret,
            "p_run_id":run_id,
            "p_run_token":run_token,
        })
        return AwarenessRun(
            run_id=str(data["run_id"]),
            run_token=run_token,
            age_band=data["age_band"],
            household_type=data["household_type"],
            answers=data.get("answers") or {},
            completed=bool(data.get("completed")),
            expires_at=datetime.fromisoformat(data["expires_at"].replace("Z","+00:00")),
            top3=data.get("top3") or [],
            findings=data.get("findings") or [],
        )

    def finalize_run(self,run_id:str,run_token:str,top3:list[dict],findings:list[dict])->dict:
        return self._rpc("rpc_awareness_finalize",{
            "p_internal_secret":self.secret,
            "p_run_id":run_id,
            "p_run_token":run_token,
            "p_top3":top3,
            "p_findings":findings,
        })

    def claim_handoff(self,handoff_token:str,subject:str)->dict:
        dashboard=self._rpc("rpc_awareness_claim",{
            "p_internal_secret":self.secret,
            "p_handoff_token":handoff_token,
            "p_auth_subject":subject,
        })
        return {"claimed":True,"idempotent":False,"dashboard":dashboard}

    def dashboard(self,subject:str)->dict:
        return self._rpc("rpc_member_dashboard",{
            "p_internal_secret":self.secret,
            "p_auth_subject":subject,
        })

def build_store():
    backend=os.getenv("LIFE2_STORAGE_BACKEND","memory").lower()
    return SupabaseRPCStore() if backend=="supabase" else MemoryStore()

store=build_store()
