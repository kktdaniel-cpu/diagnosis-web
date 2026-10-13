"""Explicit member request receipt, not booking or outbound notification."""
from typing import Literal
from uuid import UUID
from pydantic import Field, model_validator
from .income_gap import ClosedModel

class ConsultationRequest(ClosedModel):
    preparation_id: UUID
    request_id: UUID
    topic: Literal['CALENDAR','PENSION','BUDGET','WORK']
    consent: bool = Field(strict=True)

    @model_validator(mode='after')
    def agreed(self):
        if not self.consent:
            raise ValueError('상담 신청 내용 저장 동의가 필요합니다.')
        return self
