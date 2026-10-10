from fastapi import APIRouter

from .catalog import public_questions

router = APIRouter(prefix="/v1/awareness", tags=["awareness"])


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
