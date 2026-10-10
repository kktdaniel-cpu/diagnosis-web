from typing import Any, Literal
from pydantic import BaseModel, Field

Household = Literal["single","couple"]
AwarenessResponse = Literal["CONFIRMED","PARTIAL","UNKNOWN_OR_NOT_PREPARED"]

class RunCreate(BaseModel):
    age_band: str = Field(pattern=r"^[0-9A-Z_]+$")
    household_type: Household

class AnswerPut(BaseModel):
    response: AwarenessResponse

class HandoffClaim(BaseModel):
    handoff_token: str = Field(min_length=16, max_length=256)

class ActionFields(BaseModel):
    fields: dict[str, Any] = Field(default_factory=dict)


class AIHelpRequest(BaseModel):
    action_catalog_id: str = Field(min_length=3, max_length=128)
    question: str = Field(min_length=1, max_length=500)

class AIExplainRequest(BaseModel):
    action_catalog_id: str = Field(min_length=3, max_length=128)
