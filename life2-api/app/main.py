from __future__ import annotations
import os
from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from .catalog import QUESTIONS, QUESTION_BY_ID, ACTION_META
from .models import RunCreate, AnswerPut, HandoffClaim
from .store import store, StoreError
from .top3 import select_top3
from .auth import get_current_subject
from .config import cors_origins

APP_VERSION = "MVP-0.2.0"
app = FastAPI(title="LIFE 2.0 API", version=APP_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def _store_error(e: StoreError):
    raise HTTPException(status_code=e.status_code, detail={"code":e.code})

def _enrich_dashboard(data: dict) -> dict:
    enriched=[]
    for item in data.get("top3", []):
        x=dict(item)
        meta=ACTION_META.get(x.get("action_catalog_id"))
        if meta:
            x["title"]=meta[0]
        enriched.append(x)
    data=dict(data)
    data["top3"]=enriched
    return data

@app.get("/health")
def health():
    return {"ok": True, "version": APP_VERSION, "storage": os.getenv("LIFE2_STORAGE_BACKEND","memory")}

@app.get("/v1/me")
async def me(subject: str = Depends(get_current_subject)):
    return {"ok": True, "data": {"authenticated": True, "auth_subject": subject}}

@app.post("/v1/me/awareness/claim")
async def claim_awareness(payload: HandoffClaim, subject: str = Depends(get_current_subject)):
    try:
        data=store.claim_handoff(payload.handoff_token,subject)
        data=dict(data)
        data["dashboard"]=_enrich_dashboard(data.get("dashboard") or {})
    except StoreError as e:
        _store_error(e)
    return {"ok":True,"data":data}

@app.get("/v1/me/dashboard")
async def dashboard(subject: str = Depends(get_current_subject)):
    try:
        data=_enrich_dashboard(store.dashboard(subject))
    except StoreError as e:
        _store_error(e)
    return {"ok":True,"data":data}

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
    try:
        data=store.create_run(payload.age_band,payload.household_type)
    except StoreError as e:
        _store_error(e)
    return {"ok":True,"data":data}

@app.put("/v1/awareness/runs/{run_id}/answers/{question_id}")
def put_answer(
    run_id: str,
    question_id: str,
    payload: AnswerPut,
    x_awareness_token: str = Header(default=""),
):
    if question_id not in QUESTION_BY_ID:
        raise HTTPException(404,"question not found")
    if not x_awareness_token:
        raise HTTPException(403,"invalid awareness token")
    try:
        data=store.put_answer(run_id,x_awareness_token,question_id,payload.response)
    except StoreError as e:
        _store_error(e)
    return {"ok":True,"data":data}

@app.post("/v1/awareness/runs/{run_id}/complete")
def complete_run(run_id: str, x_awareness_token: str = Header(default="")):
    if not x_awareness_token:
        raise HTTPException(403,"invalid awareness token")
    try:
        run=store.get_run(run_id,x_awareness_token)
    except StoreError as e:
        _store_error(e)

    missing=[q["id"] for q in QUESTIONS if q["id"] not in run.answers]
    if missing:
        raise HTTPException(409,detail={"code":"AWARENESS_INCOMPLETE","missing":missing})

    top3=select_top3(run.answers)
    findings=[
        {
            "finding_type":f"FIND.{QUESTION_BY_ID[qid]['domain']}.{qid.lower()}",
            "status":"OPEN",
            "source_ref":qid
        }
        for qid,state in run.answers.items() if state != "CONFIRMED"
    ]
    try:
        data=store.finalize_run(run_id,x_awareness_token,top3,findings)
    except StoreError as e:
        _store_error(e)
    return {"ok":True,"data":data}
