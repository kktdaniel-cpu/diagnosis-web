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
        self.action_instances: dict[str, dict] = {}
        self.facts: dict[str, dict[str, dict]] = {}
        self.recent: dict[str, list[dict]] = {}
        self.change_events: dict[tuple[str,str], dict] = {}

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

    def member_awareness(self, subject: str) -> dict:
        run_id=self.member_run.get(subject)
        run=self.runs.get(run_id) if run_id else None
        if not run:
            raise StoreError("AWARENESS_NOT_FOUND",404)
        return {
            "run_id":run.run_id,
            "household_type":run.household_type,
            "age_band":run.age_band,
            "answers":dict(run.answers),
        }

    def member_facts(self, subject: str) -> dict:
        return dict(self.facts.get(subject, {}))

    def dashboard(self, subject: str) -> dict:
        run_id=self.member_run.get(subject)
        run=self.runs.get(run_id) if run_id else None
        if not run:
            return {"confirmed_awareness_count":0,"awareness_total":12,"top3":[],"in_progress":[],"recent_changes":[]}
        in_progress=[
            dict(x) for x in self.action_instances.values()
            if x["subject"]==subject and x["status"] in ("IN_PROGRESS","WAITING_EXTERNAL")
        ]
        top3=[]
        for original in run.top3:
            x=dict(original)
            active=next((
                a for a in self.action_instances.values()
                if a["subject"]==subject
                and a["action_catalog_id"]==x.get("action_catalog_id")
                and a["status"] in ("NOT_STARTED","IN_PROGRESS","WAITING_EXTERNAL","REVIEW_DUE")
            ),None)
            x["status"]=active["status"] if active else "NOT_STARTED"
            top3.append(x)
        return {
            "confirmed_awareness_count":sum(1 for v in run.answers.values() if v=="CONFIRMED"),
            "awareness_total":12,
            "top3":top3,
            "in_progress":in_progress,
            "recent_changes":self.recent.get(subject,[])[:5],
        }

    def start_action(self, subject: str, action_catalog_id: str, mode: str) -> dict:
        existing=next((
            x for x in self.action_instances.values()
            if x["subject"]==subject
            and x["action_catalog_id"]==action_catalog_id
            and x["status"] in ("NOT_STARTED","IN_PROGRESS","WAITING_EXTERNAL","REVIEW_DUE")
        ),None)
        if existing:
            existing["status"]="IN_PROGRESS"
            return {k:existing[k] for k in ("action_instance_id","action_catalog_id","status","mode","draft")}
        action_id=str(uuid4())
        item={
            "action_instance_id":action_id,
            "subject":subject,
            "action_catalog_id":action_catalog_id,
            "status":"IN_PROGRESS",
            "mode":mode,
            "draft":{},
        }
        self.action_instances[action_id]=item
        return {k:item[k] for k in ("action_instance_id","action_catalog_id","status","mode","draft")}

    def submit_action(self, subject: str, action_instance_id: str, fields: dict) -> dict:
        item=self.action_instances.get(action_instance_id)
        if not item or item["subject"]!=subject:
            raise StoreError("ACTION_NOT_FOUND",404)
        if item["status"] not in ("NOT_STARTED","IN_PROGRESS","WAITING_EXTERNAL","REVIEW_DUE"):
            raise StoreError("INVALID_ACTION_TRANSITION",409)
        item["status"]="IN_PROGRESS"
        item["draft"]=dict(fields)
        return {"action_instance_id":action_instance_id,"status":"IN_PROGRESS","draft":dict(fields)}

    def wait_action(self, subject: str, action_instance_id: str) -> dict:
        item=self.action_instances.get(action_instance_id)
        if not item or item["subject"]!=subject:
            raise StoreError("ACTION_NOT_FOUND",404)
        if item["status"] not in ("NOT_STARTED","IN_PROGRESS","WAITING_EXTERNAL","REVIEW_DUE"):
            raise StoreError("INVALID_ACTION_TRANSITION",409)
        item["status"]="WAITING_EXTERNAL"
        return {
            "action_instance_id":action_instance_id,
            "action_catalog_id":item["action_catalog_id"],
            "status":"WAITING_EXTERNAL",
            "mode":item["mode"],
            "draft":dict(item["draft"]),
        }

    def complete_action(
        self,
        subject: str,
        action_instance_id: str,
        action_catalog_id: str,
        question_id: str,
        facts: list[dict],
        new_top3: list[dict],
    ) -> dict:
        item=self.action_instances.get(action_instance_id)
        if not item or item["subject"]!=subject:
            raise StoreError("ACTION_NOT_FOUND",404)
        if item["action_catalog_id"]!=action_catalog_id:
            raise StoreError("ACTION_CATALOG_MISMATCH",422)
        run_id=self.member_run.get(subject)
        run=self.runs.get(run_id) if run_id else None
        if not run:
            raise StoreError("AWARENESS_NOT_FOUND",404)
        if item["status"] in ("SELF_REPORTED_DONE","VERIFIED_DONE"):
            return {"idempotent":True,"dashboard":self.dashboard(subject)}
        top3_before=[x.get("action_catalog_id") for x in run.top3]
        bucket=self.facts.setdefault(subject,{})
        for fact in facts:
            bucket[fact["fact_key"]]=dict(fact)
        item["status"]="SELF_REPORTED_DONE"
        item["draft"]={}
        run.answers[question_id]="CONFIRMED"
        run.top3=list(new_top3)
        event_id=str(uuid4())
        event={
            "event_id":event_id,
            "action_instance_id":action_instance_id,
            "action_catalog_id":action_catalog_id,
            "metadata":{
                "question_id":question_id,
                "fact_keys":[x["fact_key"] for x in facts],
                "top3_before":top3_before,
                "top3_after":[x.get("action_catalog_id") for x in new_top3],
                "top3_changed":top3_before != [x.get("action_catalog_id") for x in new_top3],
            },
            "occurred_at":datetime.now(timezone.utc).isoformat(),
        }
        self.change_events[(subject,action_instance_id)]=event
        self.recent.setdefault(subject,[]).insert(0,{
            "event_type":"ACTION_COMPLETED",
            "summary_code":action_catalog_id,
            "occurred_at":event["occurred_at"],
        })
        return {"idempotent":False,"event_id":event_id,"dashboard":self.dashboard(subject)}

    def change_event(self, subject: str, action_instance_id: str) -> dict:
        event=self.change_events.get((subject,action_instance_id))
        if not event:
            raise StoreError("CHANGE_EVENT_NOT_FOUND",404)
        return dict(event)

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
                headers={
                    "apikey":self.key,
                    "Content-Type":"application/json",
                    "X-Life2-Internal-Secret":self.secret,
                },
                json=payload,
                timeout=8.0,
            )
        except httpx.HTTPError as e:
            raise StoreError("STORAGE_UNAVAILABLE",503) from e
        if r.status_code >= 400:
            try:
                msg=r.json().get("message","")
            except Exception:
                msg=r.text
            lower=str(msg).lower()
            code,status="STORAGE_ERROR",500
            if "expired" in lower:
                code,status="RUN_EXPIRED",410
            elif "handoff already claimed" in lower:
                code,status="HANDOFF_ALREADY_CLAIMED",409
            elif "handoff not found" in lower:
                code,status="HANDOFF_NOT_FOUND",404
            elif "action not found" in lower:
                code,status="ACTION_NOT_FOUND",404
            elif "catalog mismatch" in lower:
                code,status="ACTION_CATALOG_MISMATCH",422
            elif "awareness not found" in lower:
                code,status="AWARENESS_NOT_FOUND",404
            elif "forbidden" in lower:
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
        return self._rpc("rpc_awareness_claim",{
            "p_internal_secret":self.secret,
            "p_handoff_token":handoff_token,
            "p_auth_subject":subject,
        })

    def member_awareness(self,subject:str)->dict:
        return self._rpc("rpc_member_awareness",{
            "p_internal_secret":self.secret,
            "p_auth_subject":subject,
        })

    def member_facts(self,subject:str)->dict:
        return self._rpc("rpc_member_facts",{
            "p_internal_secret":self.secret,
            "p_auth_subject":subject,
        })

    def dashboard(self,subject:str)->dict:
        return self._rpc("rpc_member_dashboard",{
            "p_internal_secret":self.secret,
            "p_auth_subject":subject,
        })

    def start_action(self,subject:str,action_catalog_id:str,mode:str)->dict:
        return self._rpc("rpc_action_start",{
            "p_internal_secret":self.secret,
            "p_auth_subject":subject,
            "p_action_catalog_id":action_catalog_id,
            "p_mode":mode,
        })

    def submit_action(self,subject:str,action_instance_id:str,fields:dict)->dict:
        return self._rpc("rpc_action_submit",{
            "p_internal_secret":self.secret,
            "p_auth_subject":subject,
            "p_action_instance_id":action_instance_id,
            "p_draft":fields,
        })

    def wait_action(self,subject:str,action_instance_id:str)->dict:
        return self._rpc("rpc_action_wait",{
            "p_internal_secret":self.secret,
            "p_auth_subject":subject,
            "p_action_instance_id":action_instance_id,
        })

    def change_event(self,subject:str,action_instance_id:str)->dict:
        return self._rpc("rpc_action_change_event",{
            "p_internal_secret":self.secret,
            "p_auth_subject":subject,
            "p_action_instance_id":action_instance_id,
        })

    def complete_action(
        self,
        subject:str,
        action_instance_id:str,
        action_catalog_id:str,
        question_id:str,
        facts:list[dict],
        new_top3:list[dict],
    )->dict:
        return self._rpc("rpc_action_complete",{
            "p_internal_secret":self.secret,
            "p_auth_subject":subject,
            "p_action_instance_id":action_instance_id,
            "p_action_catalog_id":action_catalog_id,
            "p_question_id":question_id,
            "p_fact_rows":facts,
            "p_new_top3":new_top3,
        })

def build_store():
    backend=os.getenv("LIFE2_STORAGE_BACKEND","memory").lower()
    return SupabaseRPCStore() if backend=="supabase" else MemoryStore()

store=build_store()
