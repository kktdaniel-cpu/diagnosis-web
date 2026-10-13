"""Explicitly consented preparation drafts, never completed Action FACTs."""
from typing import Annotated
from pydantic import Field, model_validator
from .income_gap import ClosedModel, IncomeGapInput, build_preview


class GapSaveRequest(ClosedModel):
    answers: IncomeGapInput
    consent: Annotated[bool, Field(strict=True)]

    @model_validator(mode="after")
    def agreed(self):
        if not self.consent:
            raise ValueError("준비 초안 저장 동의가 필요합니다.")
        return self


def saved_preview(record):
    if record is None:
        return None
    result = build_preview(IncomeGapInput(**record['answers']))
    result.update(preparation_id=record['preparation_id'], persistence='MEMBER_PREPARATION',
                  saved_at=record['saved_at'], fact_writes=False)
    result['notes'][-1] = 'MY LIFE에 저장한 준비 초안입니다. 확정 FACT나 Action 확인 완료가 아닙니다.'
    return result
