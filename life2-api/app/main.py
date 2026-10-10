from __future__ import annotations
from datetime import datetime, timezone
from secrets import token_urlsafe
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from .catalog import QUESTIONS, QUESTION_BY_ID
from .models import RunCreate, AnswerPut
from .store import store
from .top3 import select_top3

APP_VERSION = "MVP-0.1.1"
app = FastAPI(title="LIFE 2.0 API", version=APP_VERSION)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"ok": True, "version": APP_VERSION}

@app.get("/v1/awareness/questions")
def questions(household_type: str = "single"):
    if household_type not in {"single","couple"}:
        raise HTTPException(422, "invalid household_type")
    data=[]
    for q in QUESTIONS:
        text = q.get("q_couple") if household_type == "couple" and q.get("q_couple") else q.get("q_single") or q.get("q")
        data.append({"id":q["id"],"domain":q["domain"],"q":text,"responses":q["responses"]})
    return {"ok":True,"data":{"schema_version":"1.0","questions":data,"total":12}}

@app.post("/v1/awareness/runs")
def create_run(payload: RunCreate):
    run=store.create_run(payload.age_band,payload.household_type)
    return {"ok":True,"data":{"run_id":run.run_id,"run_token":run.run_token,"expires_at":run.expires_at.isoformat()}}

@app.put("/v1/awareness/runs/{run_id}/answers/{question_id}")
def put_answer(
    run_id: str,
    question_id: str,
    payload: AnswerPut,
    x_awareness_token: str = Header(default=""),
):
    run=store.get_run(run_id)
    if not run:
        raise HTTPException(404,"run not found")
    if not x_awareness_token or x_awareness_token != run.run_token:
        raise HTTPException(403,"invalid awareness token")
    if run.completed:
        raise HTTPException(409,"run already completed")
    if datetime.now(timezone.utc) > run.expires_at:
        raise HTTPException(410,"run expired")
    if question_id not in QUESTION_BY_ID:
        raise HTTPException(404,"question not found")
    run.answers[question_id]=payload.response
    return {"ok":True,"data":{"saved":True,"answered":len(run.answers),"total":12}}

@app.post("/v1/awareness/runs/{run_id}/complete")
def complete_run(run_id: str, x_awareness_token: str = Header(default="")):
    run=store.get_run(run_id)
    if not run:
        raise HTTPException(404,"run not found")
    if not x_awareness_token or x_awareness_token != run.run_token:
        raise HTTPException(403,"invalid awareness token")
    missing=[q["id"] for q in QUESTIONS if q["id"] not in run.answers]
    if missing:
        raise HTTPException(409,detail={"code":"AWARENESS_INCOMPLETE","missing":missing})
    if run.completed:
        top3=select_top3(run.answers)
        return {"ok":True,"data":{"top3":top3,"handoff_token":run.handoff_token,"idempotent":True}}
    run.completed=True
    run.handoff_token=token_urlsafe(32)
    top3=select_top3(run.answers)
    findings=[
        {
            "finding_type":f"FIND.{QUESTION_BY_ID[qid]['domain']}.{qid.lower()}",
            "status":"OPEN",
            "source_ref":qid
        }
        for qid,state in run.answers.items() if state != "CONFIRMED"
    ]
    return {"ok":True,"data":{"findings":findings,"top3":top3,"handoff_token":run.handoff_token}}
