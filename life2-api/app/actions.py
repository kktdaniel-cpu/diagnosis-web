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
    "ACT_CHECK_RET_PRIVATE_PENSION": {
        "question_id": "AWR_Q03_RET_PRIVATE_PENSION",
        "title": "퇴직·개인연금 확인하기",
        "description": "국민연금을 제외한 퇴직연금·IRP·개인연금의 월 수령액, 개시 나이, 수령 기간을 확인합니다.",
        "fields": [
            {
                "key": "has_ret_private_pension",
                "label": "퇴직·개인연금이 있나요?",
                "type": "select",
                "required": True,
                "options": [
                    {"value":"YES","label":"있음"},
                    {"value":"NO","label":"없음"},
                ],
            },
            {
                "key": "ret_private_monthly_10k",
                "label": "부부합산 예상 월 수령액",
                "type": "integer",
                "unit": "만원/월",
                "min": 0,
                "max": 3000,
                "required": True,
                "show_when": {"key":"has_ret_private_pension","value":"YES"},
            },
            {
                "key": "ret_private_start_age",
                "label": "수령 개시 나이",
                "type": "integer",
                "unit": "세",
                "min": 55,
                "max": 95,
                "required": True,
                "show_when": {"key":"has_ret_private_pension","value":"YES"},
            },
            {
                "key": "ret_private_years",
                "label": "수령 기간",
                "type": "integer",
                "unit": "년",
                "min": 1,
                "max": 50,
                "required": True,
                "show_when": {"key":"has_ret_private_pension","value":"YES"},
            },
        ],
    },
    "ACT_ESTIMATE_RETIREMENT_BUDGET": {
        "question_id": "AWR_Q04_RETIREMENT_BUDGET",
        "title": "은퇴 생활비 계산하기",
        "description": "65세 이후 우리 집이 매달 필요하다고 생각하는 생활비를 현재 계획 기준으로 적습니다.",
        "fields": [
            {
                "key": "retirement_budget_10k",
                "label": "65세 이후 목표 월 생활비",
                "type": "integer",
                "unit": "만원/월",
                "min": 50,
                "max": 3000,
                "required": True,
            }
        ],
    },
    "ACT_SUMMARIZE_ASSETS_DEBT": {
        "question_id": "AWR_Q06_ASSETS_DEBT",
        "title": "자산·부채 한눈에 정리하기",
        "description": "정확한 금액을 새로 만들지 않고, 기존 정밀진단과 같은 구간으로 금융자산과 대출 규모를 확인합니다.",
        "fields": [
            {
                "key": "financial_asset_band",
                "label": "현금화 가능한 금융자산 규모",
                "type": "select",
                "required": True,
                "options": [
                    {"value":"LT_30M","label":"3,000만 원 미만"},
                    {"value":"30M_100M","label":"3,000만 ~ 1억 원"},
                    {"value":"100M_200M","label":"1억 ~ 2억 원"},
                    {"value":"200M_300M","label":"2억 ~ 3억 원"},
                    {"value":"GE_300M","label":"3억 원 이상"},
                ],
            },
            {
                "key": "debt_band",
                "label": "현재 남아있는 대출 총액",
                "type": "select",
                "required": True,
                "options": [
                    {"value":"NONE","label":"없음"},
                    {"value":"LT_100M","label":"1억 원 미만"},
                    {"value":"100M_300M","label":"1억 ~ 3억 원 미만"},
                    {"value":"300M_500M","label":"3억 ~ 5억 원 미만"},
                    {"value":"GE_500M","label":"5억 원 이상"},
                ],
            },
        ],
    },
    "ACT_DEFINE_POST_RETIREMENT_WORK": {
        "question_id": "AWR_Q07_POST_RETIREMENT_WORK",
        "title": "퇴직 후 일자리 계획 만들기",
        "description": "퇴직 후 일할 형태, 예상 월 근로소득, 소득활동 종료 나이를 현재 계획 기준으로 정합니다.",
        "fields": [
            {
                "key": "work_plan_type",
                "label": "퇴직 후 일할 계획·형태",
                "type": "select",
                "required": True,
                "options": [
                    {"value":"FULL_TIME","label":"풀타임 재취업 (전일제)"},
                    {"value":"PART_TIME_GIG","label":"주 2~3일 파트타임 · 긱워커"},
                    {"value":"SELF_EMPLOYED","label":"창업 · 자영업 · 프리랜서"},
                    {"value":"NO_WORK","label":"일하지 않을 계획"},
                ],
            },
            {
                "key": "post_retirement_income_10k",
                "label": "퇴직 후 예상 월 근로소득",
                "type": "integer",
                "unit": "만원/월",
                "min": 0,
                "max": 5000,
                "required": True,
                "show_when_not": {"key":"work_plan_type","value":"NO_WORK"},
            },
            {
                "key": "work_end_age",
                "label": "소득활동 종료 나이",
                "type": "integer",
                "unit": "세",
                "min": 45,
                "max": 95,
                "required": True,
                "show_when_not": {"key":"work_plan_type","value":"NO_WORK"},
            },
            {
                "key": "health_insurance_type",
                "label": "재취업 후 건강보험 가입 형태",
                "type": "select",
                "required": True,
                "show_when_not": {"key":"work_plan_type","value":"NO_WORK"},
                "options": [
                    {"value":"EMPLOYEE","label":"직장가입"},
                    {"value":"REGIONAL","label":"지역가입 · 개인"},
                    {"value":"UNKNOWN","label":"잘 모름"},
                ],
            },
        ],
    },
    "ACT_DEFINE_CARE_PLAN": {
        "question_id": "AWR_Q10_CARE",
        "title": "돌봄 비용·방법 체크하기",
        "description": "장기 돌봄이 필요할 때 누가 돌볼지, 어디에서 돌봄을 받을지, 비용을 어느 구간으로 준비할지 정합니다.",
        "fields": [
            {
                "key": "care_provider",
                "label": "주된 돌봄 담당",
                "type": "select",
                "required": True,
                "options": [
                    {"value":"FAMILY","label":"가족 중심"},
                    {"value":"PROFESSIONAL","label":"전문 돌봄인력 중심"},
                    {"value":"MIXED","label":"가족 + 전문 돌봄인력"},
                ],
            },
            {
                "key": "care_place",
                "label": "주된 돌봄 장소",
                "type": "select",
                "required": True,
                "options": [
                    {"value":"HOME","label":"현재 집 또는 가족 집"},
                    {"value":"FACILITY","label":"요양시설 · 돌봄시설"},
                    {"value":"MIXED","label":"상황에 따라 병행"},
                ],
            },
            {
                "key": "care_cost_band",
                "label": "월 돌봄비 준비 구간",
                "type": "select",
                "required": True,
                "options": [
                    {"value":"LT_1M","label":"월 100만 원 미만"},
                    {"value":"1M_2M","label":"월 100만 ~ 200만 원"},
                    {"value":"2M_3M","label":"월 200만 ~ 300만 원"},
                    {"value":"GE_3M","label":"월 300만 원 이상"},
                ],
            },
            {
                "key": "care_coverage_status",
                "label": "장기요양·간병 대비 상태",
                "type": "select",
                "required": True,
                "options": [
                    {"value":"INSUFFICIENT","label":"부족함 / 미가입"},
                    {"value":"RESEARCHING","label":"필요성 느낌 · 알아보는 중"},
                    {"value":"PREPARED","label":"간병·장기요양 보장 준비 완료"},
                ],
            },
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

def _choice_field(fields: dict[str, Any], key: str, allowed: set[str]) -> str:
    raw = fields.get(key)
    if raw in (None, ""):
        raise ActionValidationError("REQUIRED", key)
    value = str(raw)
    if value not in allowed:
        raise ActionValidationError("INVALID_CHOICE", key)
    return value

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

    if action_catalog_id == "ACT_CHECK_RET_PRIVATE_PENSION":
        has_pen=_choice_field(fields,"has_ret_private_pension",{"YES","NO"})
        facts=[
            {
                "fact_key":"pension.ret_private.exists",
                "status":"KNOWN",
                "value":has_pen=="YES",
                "unit":"boolean",
                "source_type":"USER_CONFIRMED",
                "source_ref":"ACT_CHECK_RET_PRIVATE_PENSION",
                "verification_level":"SELF_REPORTED",
            }
        ]
        normalized={"has_ret_private_pension":has_pen}
        if has_pen=="YES":
            monthly=_int_field(fields,"ret_private_monthly_10k",0,3000)
            start=_int_field(fields,"ret_private_start_age",55,95)
            years=_int_field(fields,"ret_private_years",1,50)
            end=start+years
            normalized.update({
                "ret_private_monthly_10k":monthly,
                "ret_private_start_age":start,
                "ret_private_years":years,
                "ret_private_end_age":end,
            })
            facts.extend([
                {
                    "fact_key":"pension.ret_private.monthly_household",
                    "status":"KNOWN",
                    "value":monthly,
                    "unit":"10k_KRW_per_month",
                    "source_type":"USER_CONFIRMED",
                    "source_ref":"ACT_CHECK_RET_PRIVATE_PENSION",
                    "verification_level":"SELF_REPORTED",
                },
                {
                    "fact_key":"pension.ret_private.start_age",
                    "status":"KNOWN",
                    "value":start,
                    "unit":"age_years",
                    "source_type":"USER_CONFIRMED",
                    "source_ref":"ACT_CHECK_RET_PRIVATE_PENSION",
                    "verification_level":"SELF_REPORTED",
                },
                {
                    "fact_key":"pension.ret_private.duration_years",
                    "status":"KNOWN",
                    "value":years,
                    "unit":"years",
                    "source_type":"USER_CONFIRMED",
                    "source_ref":"ACT_CHECK_RET_PRIVATE_PENSION",
                    "verification_level":"SELF_REPORTED",
                },
                {
                    "fact_key":"pension.ret_private.end_age",
                    "status":"KNOWN",
                    "value":end,
                    "unit":"age_years",
                    "source_type":"RULE_DERIVED",
                    "source_ref":"RULE_RETPEN_END_AGE_V1",
                    "verification_level":"RULE_DERIVED",
                },
            ])
        return {
            "question_id":"AWR_Q03_RET_PRIVATE_PENSION",
            "normalized":normalized,
            "facts":facts,
        }

    if action_catalog_id == "ACT_ESTIMATE_RETIREMENT_BUDGET":
        budget=_int_field(fields,"retirement_budget_10k",50,3000)
        return {
            "question_id":"AWR_Q04_RETIREMENT_BUDGET",
            "normalized":{"retirement_budget_10k":budget},
            "facts":[
                {
                    "fact_key":"cashflow.retirement_monthly_budget_target",
                    "status":"KNOWN",
                    "value":budget,
                    "unit":"10k_KRW_per_month",
                    "source_type":"USER_CONFIRMED",
                    "source_ref":"ACT_ESTIMATE_RETIREMENT_BUDGET",
                    "verification_level":"SELF_REPORTED",
                }
            ],
        }

    if action_catalog_id == "ACT_SUMMARIZE_ASSETS_DEBT":
        asset=_choice_field(fields,"financial_asset_band",{
            "LT_30M","30M_100M","100M_200M","200M_300M","GE_300M"
        })
        debt=_choice_field(fields,"debt_band",{
            "NONE","LT_100M","100M_300M","300M_500M","GE_500M"
        })
        return {
            "question_id":"AWR_Q06_ASSETS_DEBT",
            "normalized":{"financial_asset_band":asset,"debt_band":debt},
            "facts":[
                {
                    "fact_key":"asset.financial_liquid_band_q23",
                    "status":"KNOWN",
                    "value":asset,
                    "unit":"Q23_band",
                    "source_type":"USER_CONFIRMED",
                    "source_ref":"ACT_SUMMARIZE_ASSETS_DEBT",
                    "verification_level":"SELF_REPORTED",
                },
                {
                    "fact_key":"debt.total_band_q30",
                    "status":"KNOWN",
                    "value":debt,
                    "unit":"Q30_band",
                    "source_type":"USER_CONFIRMED",
                    "source_ref":"ACT_SUMMARIZE_ASSETS_DEBT",
                    "verification_level":"SELF_REPORTED",
                },
            ],
        }

    if action_catalog_id == "ACT_DEFINE_POST_RETIREMENT_WORK":
        plan=_choice_field(fields,"work_plan_type",{
            "FULL_TIME","PART_TIME_GIG","SELF_EMPLOYED","NO_WORK"
        })
        normalized={"work_plan_type":plan}
        facts=[
            {
                "fact_key":"work.post_retirement.plan_type",
                "status":"KNOWN",
                "value":plan,
                "unit":"Q31_choice",
                "source_type":"USER_CONFIRMED",
                "source_ref":"ACT_DEFINE_POST_RETIREMENT_WORK",
                "verification_level":"SELF_REPORTED",
            }
        ]
        if plan=="NO_WORK":
            normalized["post_retirement_income_10k"]=0
            facts.append({
                "fact_key":"work.post_retirement.monthly_income",
                "status":"KNOWN",
                "value":0,
                "unit":"10k_KRW_per_month",
                "source_type":"USER_CONFIRMED",
                "source_ref":"ACT_DEFINE_POST_RETIREMENT_WORK:NO_WORK",
                "verification_level":"SELF_REPORTED",
            })
        else:
            income=_int_field(fields,"post_retirement_income_10k",0,5000)
            end_age=_int_field(fields,"work_end_age",45,95)
            hins=_choice_field(fields,"health_insurance_type",{"EMPLOYEE","REGIONAL","UNKNOWN"})
            normalized.update({
                "post_retirement_income_10k":income,
                "work_end_age":end_age,
                "health_insurance_type":hins,
            })
            facts.extend([
                {
                    "fact_key":"work.post_retirement.monthly_income",
                    "status":"KNOWN",
                    "value":income,
                    "unit":"10k_KRW_per_month",
                    "source_type":"USER_CONFIRMED",
                    "source_ref":"ACT_DEFINE_POST_RETIREMENT_WORK",
                    "verification_level":"SELF_REPORTED",
                },
                {
                    "fact_key":"work.income_end_age",
                    "status":"KNOWN",
                    "value":end_age,
                    "unit":"age_years",
                    "source_type":"USER_CONFIRMED",
                    "source_ref":"ACT_DEFINE_POST_RETIREMENT_WORK",
                    "verification_level":"SELF_REPORTED",
                },
                {
                    "fact_key":"work.post_retirement.health_insurance_type",
                    "status":"UNKNOWN" if hins=="UNKNOWN" else "KNOWN",
                    "value":hins,
                    "unit":"Q31A_choice",
                    "source_type":"USER_CONFIRMED",
                    "source_ref":"ACT_DEFINE_POST_RETIREMENT_WORK",
                    "verification_level":"SELF_REPORTED",
                },
            ])
        return {
            "question_id":"AWR_Q07_POST_RETIREMENT_WORK",
            "normalized":normalized,
            "facts":facts,
        }

    if action_catalog_id == "ACT_DEFINE_CARE_PLAN":
        provider=_choice_field(fields,"care_provider",{"FAMILY","PROFESSIONAL","MIXED"})
        place=_choice_field(fields,"care_place",{"HOME","FACILITY","MIXED"})
        cost=_choice_field(fields,"care_cost_band",{"LT_1M","1M_2M","2M_3M","GE_3M"})
        coverage=_choice_field(fields,"care_coverage_status",{"INSUFFICIENT","RESEARCHING","PREPARED"})
        return {
            "question_id":"AWR_Q10_CARE",
            "normalized":{
                "care_provider":provider,
                "care_place":place,
                "care_cost_band":cost,
                "care_coverage_status":coverage,
            },
            "facts":[
                {
                    "fact_key":"care.primary_provider_plan",
                    "status":"KNOWN",
                    "value":provider,
                    "unit":"care_provider_choice",
                    "source_type":"USER_CONFIRMED",
                    "source_ref":"ACT_DEFINE_CARE_PLAN",
                    "verification_level":"SELF_REPORTED",
                },
                {
                    "fact_key":"care.primary_place_plan",
                    "status":"KNOWN",
                    "value":place,
                    "unit":"care_place_choice",
                    "source_type":"USER_CONFIRMED",
                    "source_ref":"ACT_DEFINE_CARE_PLAN",
                    "verification_level":"SELF_REPORTED",
                },
                {
                    "fact_key":"care.monthly_cost_band",
                    "status":"KNOWN",
                    "value":cost,
                    "unit":"care_cost_band",
                    "source_type":"USER_CONFIRMED",
                    "source_ref":"ACT_DEFINE_CARE_PLAN",
                    "verification_level":"SELF_REPORTED",
                },
                {
                    "fact_key":"care.coverage_status_q14",
                    "status":"KNOWN",
                    "value":coverage,
                    "unit":"Q14_choice",
                    "source_type":"USER_CONFIRMED",
                    "source_ref":"ACT_DEFINE_CARE_PLAN",
                    "verification_level":"SELF_REPORTED",
                },
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
