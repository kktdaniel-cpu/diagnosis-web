from __future__ import annotations

from dataclasses import dataclass
from typing import Any

class ActionValidationError(ValueError):
    def __init__(self, code: str, field: str | None = None):
        super().__init__(code)
        self.code = code
        self.field = field

def nps_normal_start_age(birth_year: int) -> int:
    if birth_year <= 1952:
        return 60
    if birth_year <= 1956:
        return 61
    if birth_year <= 1960:
        return 62
    if birth_year <= 1964:
        return 63
    if birth_year <= 1968:
        return 64
    return 65

ACTION_FORMS: dict[str, dict[str, Any]] = {
    "ACT_CONFIRM_RETIREMENT_AGE": {
        "question_id": "AWR_Q01_RETIREMENT_AGE",
        "title": "퇴직 예상시점 정하기",
        "description": "주된 직장을 그만둘 것으로 예상하는 나이를 먼저 정합니다. 정확한 날짜가 아니라 현재 계획 기준이면 충분합니다.",
        "fields": [
            {
                "key": "retirement_age",
                "label": "주된 직장 퇴직 예상 나이",
                "type": "integer",
                "unit": "세",
                "min": 45,
                "max": 80,
                "required": True,
            }
        ],
    },
    "ACT_CHECK_NPS_ESTIMATE": {
        "question_id": "AWR_Q02_NPS",
        "title": "국민연금 예상액 확인하기",
        "description": "국민연금 예상조회에서 확인한 월 예상액을 적습니다. 수령 시작 나이는 출생연도로 계산합니다.",
        "fields": [
            {
                "key": "birth_year_self",
                "label": "본인 출생연도",
                "type": "integer",
                "unit": "년",
                "min": 1940,
                "max": 2010,
                "required": True,
            },
            {
                "key": "nps_monthly_self",
                "label": "본인 국민연금 월 예상액",
                "type": "integer",
                "unit": "원/월",
                "min": 0,
                "max": 20000000,
                "required": True,
            },
            {
                "key": "birth_year_spouse",
                "label": "배우자 출생연도",
                "type": "integer",
                "unit": "년",
                "min": 1940,
                "max": 2010,
                "required_when": "household_type=couple",
            },
            {
                "key": "nps_monthly_spouse",
                "label": "배우자 국민연금 월 예상액",
                "type": "integer",
                "unit": "원/월",
                "min": 0,
                "max": 20000000,
                "required_when": "household_type=couple",
            },
        ],
    },
}

SUPPORTED_ACTIONS = set(ACTION_FORMS)

def _int_field(fields: dict[str, Any], key: str, lo: int, hi: int, required: bool = True) -> int | None:
    raw = fields.get(key)
    if raw in (None, ""):
        if required:
            raise ActionValidationError("REQUIRED", key)
        return None
    if isinstance(raw, bool):
        raise ActionValidationError("INVALID_INTEGER", key)
    try:
        value = int(raw)
    except (TypeError, ValueError):
        raise ActionValidationError("INVALID_INTEGER", key)
    if value < lo or value > hi:
        raise ActionValidationError("OUT_OF_RANGE", key)
    return value

def form_for(action_catalog_id: str, household_type: str) -> dict[str, Any]:
    if action_catalog_id not in ACTION_FORMS:
        raise ActionValidationError("ACTION_NOT_SUPPORTED")
    form = ACTION_FORMS[action_catalog_id]
    fields=[]
    for f in form["fields"]:
        x=dict(f)
        if x.get("required_when") == "household_type=couple":
            x["required"] = household_type == "couple"
        fields.append(x)
    return {
        "action_catalog_id": action_catalog_id,
        "question_id": form["question_id"],
        "title": form["title"],
        "description": form["description"],
        "fields": fields,
    }

def prepare_completion(
    action_catalog_id: str,
    fields: dict[str, Any],
    household_type: str,
) -> dict[str, Any]:
    if action_catalog_id == "ACT_CONFIRM_RETIREMENT_AGE":
        retirement_age=_int_field(fields,"retirement_age",45,80)
        return {
            "question_id":"AWR_Q01_RETIREMENT_AGE",
            "normalized":{"retirement_age":retirement_age},
            "facts":[
                {
                    "fact_key":"work.primary_job_exit_age",
                    "status":"KNOWN",
                    "value":retirement_age,
                    "unit":"age_years",
                    "source_type":"USER_CONFIRMED",
                    "source_ref":"ACT_CONFIRM_RETIREMENT_AGE",
                    "verification_level":"SELF_REPORTED",
                }
            ],
        }

    if action_catalog_id == "ACT_CHECK_NPS_ESTIMATE":
        birth_self=_int_field(fields,"birth_year_self",1940,2010)
        monthly_self=_int_field(fields,"nps_monthly_self",0,20000000)
        normalized={
            "birth_year_self":birth_self,
            "nps_monthly_self":monthly_self,
            "nps_start_age_self":nps_normal_start_age(birth_self),
        }
        facts=[
            {
                "fact_key":"profile.birth_year_self",
                "status":"KNOWN",
                "value":birth_self,
                "unit":"year",
                "source_type":"USER_CONFIRMED",
                "source_ref":"ACT_CHECK_NPS_ESTIMATE",
                "verification_level":"SELF_REPORTED",
            },
            {
                "fact_key":"pension.nps.monthly_self",
                "status":"KNOWN",
                "value":monthly_self,
                "unit":"KRW_per_month",
                "source_type":"USER_CONFIRMED",
                "source_ref":"ACT_CHECK_NPS_ESTIMATE",
                "verification_level":"SELF_REPORTED",
            },
            {
                "fact_key":"pension.nps.start_age_self",
                "status":"KNOWN",
                "value":nps_normal_start_age(birth_self),
                "unit":"age_years",
                "source_type":"RULE_DERIVED",
                "source_ref":"RULE_NPS_NORMAL_START_AGE_V1",
                "verification_level":"RULE_DERIVED",
            },
        ]

        if household_type == "couple":
            birth_spouse=_int_field(fields,"birth_year_spouse",1940,2010)
            monthly_spouse=_int_field(fields,"nps_monthly_spouse",0,20000000)
            normalized.update({
                "birth_year_spouse":birth_spouse,
                "nps_monthly_spouse":monthly_spouse,
                "nps_start_age_spouse":nps_normal_start_age(birth_spouse),
            })
            facts.extend([
                {
                    "fact_key":"profile.birth_year_spouse",
                    "status":"KNOWN",
                    "value":birth_spouse,
                    "unit":"year",
                    "source_type":"USER_CONFIRMED",
                    "source_ref":"ACT_CHECK_NPS_ESTIMATE",
                    "verification_level":"SELF_REPORTED",
                },
                {
                    "fact_key":"pension.nps.monthly_spouse",
                    "status":"KNOWN",
                    "value":monthly_spouse,
                    "unit":"KRW_per_month",
                    "source_type":"USER_CONFIRMED",
                    "source_ref":"ACT_CHECK_NPS_ESTIMATE",
                    "verification_level":"SELF_REPORTED",
                },
                {
                    "fact_key":"pension.nps.start_age_spouse",
                    "status":"KNOWN",
                    "value":nps_normal_start_age(birth_spouse),
                    "unit":"age_years",
                    "source_type":"RULE_DERIVED",
                    "source_ref":"RULE_NPS_NORMAL_START_AGE_V1",
                    "verification_level":"RULE_DERIVED",
                },
            ])

        return {
            "question_id":"AWR_Q02_NPS",
            "normalized":normalized,
            "facts":facts,
        }

    raise ActionValidationError("ACTION_NOT_SUPPORTED")
