from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Header, HTTPException, status

from ..db import get_pool
from ..schemas import AwarenessAnswerWrite, AwarenessRunCreate
from ..security import new_opaque_token, token_hash
from .catalog import AWARENESS_QUESTIONS, public_questions

router = APIRouter(prefix="/v1/awareness", tags=["awareness"])

QUESTION_BY_ID = {q["id"]: q for q in AWARENESS_QUESTIONS}


@router.get("/questions")
def questions() -> dict:
    return {
        "schema_version": "1.0",
        "metadata": [
            {
                "id": "AGE_BAND",
                "options": ["UNDER_45", "45_49", "50_55", "56_59", "60_64", "65_PLUS"],
            },
            {
                "id": "HOUSEHOLD_TYPE",
                "options": ["single", "couple"],
            },
        ],
        "questions": public_questions(),
        "total": 12,
        "rules": {
            "awareness_creates_numeric_fact": False,
            "unknown_is_zero": False,
        },
    }


@router.post("/runs", status_code=status.HTTP_201_CREATED)
async def create_run(payload: AwarenessRunCreate) -> dict:
    pool = await get_pool()
    token = new_opaque_token()
    digest = token_hash(token)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=2)

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            insert into public.awareness_runs
              (age_band, household_type, run_token_hash, expires_at)
            values ($1, $2, $3, $4)
            returning id, expires_at
            """,
            payload.age_band,
            payload.household_type.value,
            digest,
            expires_at,
        )

    return {
        "run_id": row["id"],
        "run_token": token,
        "expires_at": row["expires_at"],
    }


def _validate_question_response(question_id: str, response: str) -> None:
    question = QUESTION_BY_ID.get(question_id)
    if not question:
        raise HTTPException(status_code=404, detail="NOT_FOUND")

    allowed = {option["value"] for option in question["options"]}
    if response not in allowed:
        raise HTTPException(status_code=422, detail="INVALID_AWARENESS_RESPONSE")


@router.put("/runs/{run_id}/answers/{question_id}")
async def save_answer(
    run_id: str,
    question_id: str,
    payload: AwarenessAnswerWrite,
    x_awareness_token: str | None = Header(default=None, alias="X-Awareness-Token"),
) -> dict:
    if not x_awareness_token:
        raise HTTPException(status_code=401, detail="UNAUTHORIZED")

    _validate_question_response(question_id, payload.response.value)
    pool = await get_pool()
    digest = token_hash(x_awareness_token)

    async with pool.acquire() as conn:
        async with conn.transaction():
            run = await conn.fetchrow(
                """
                select id, expires_at, claimed_at
                from public.awareness_runs
                where id = $1 and run_token_hash = $2
                for update
                """,
                run_id,
                digest,
            )
            if not run:
                raise HTTPException(status_code=401, detail="UNAUTHORIZED")
            if run["claimed_at"] is not None:
                raise HTTPException(status_code=409, detail="HANDOFF_ALREADY_CLAIMED")
            if run["expires_at"] <= datetime.now(timezone.utc):
                raise HTTPException(status_code=410, detail="HANDOFF_EXPIRED")

            await conn.execute(
                """
                insert into public.awareness_answers (run_id, question_id, response)
                values ($1, $2, $3)
                on conflict (run_id, question_id)
                do update set response = excluded.response, updated_at = now()
                """,
                run_id,
                question_id,
                payload.response.value,
            )
            answered = await conn.fetchval(
                "select count(*) from public.awareness_answers where run_id = $1",
                run_id,
            )

    return {"saved": True, "answered": answered, "total": 12}
