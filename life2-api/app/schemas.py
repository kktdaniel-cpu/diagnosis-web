from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class AwarenessResponse(StrEnum):
    CONFIRMED = "CONFIRMED"
    PARTIAL = "PARTIAL"
    UNKNOWN_OR_NOT_PREPARED = "UNKNOWN_OR_NOT_PREPARED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class HouseholdType(StrEnum):
    SINGLE = "single"
    COUPLE = "couple"


class AwarenessRunCreate(BaseModel):
    age_band: str = Field(min_length=1, max_length=32)
    household_type: HouseholdType


class AwarenessAnswerWrite(BaseModel):
    response: AwarenessResponse


class FactStatus(StrEnum):
    KNOWN = "KNOWN"
    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    INVALID = "INVALID"
    STALE = "STALE"


class ActionStatus(StrEnum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    WAITING_EXTERNAL = "WAITING_EXTERNAL"
    SELF_REPORTED_DONE = "SELF_REPORTED_DONE"
    VERIFIED_DONE = "VERIFIED_DONE"
    REVIEW_DUE = "REVIEW_DUE"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class ActionFieldValue(BaseModel):
    status: FactStatus
    value: Any | None = None


class ActionSubmit(BaseModel):
    fields: dict[str, ActionFieldValue]
