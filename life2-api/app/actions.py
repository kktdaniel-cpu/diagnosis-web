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
    "ACT_CALCULATE_INCOME_GAP": {
        "question_id": "AWR_Q05_INCOME_GAP",
        "title": "내 소득공백 계산하기",
        "description": "퇴직 예상 나이와 본인 국민연금 개시 나이 사이의 기간을 계산하고, 그 기간을 무엇으로 연결할지 정합니다. 월 부족액은 이번 MVP에서 임의 계산하지 않습니다.",
        "fields": [
            {
                "key": "bridge_sources",
                "label": "소득공백을 연결할 수단",
                "type": "multi_select",
                "required": True,
                "options": [
                    {"value":"POST_RETIREMENT_WORK","label":"퇴직 후 근로소득"},
                    {"value":"RET_PRIVATE_PENSION","label":"퇴직·개인연금"},
                    {"value":"FINANCIAL_ASSETS","label":"금융자산 인출"},
                    {"value":"SPOUSE_INCOME","label":"배우자 소득·연금"},
                    {"value":"OTHER","label":"기타 계획"},
                ],
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
    "ACT_DEFINE_HOUSING_PLAN": {
        "question_id": "AWR_Q08_HOUSING",
        "title": "은퇴 후 주거 전략 정리하기",
        "description": "현재 거주형태와 노후 이동 방향을 정리합니다. 자가인 경우 주택연금 활용 방향도 함께 확인합니다.",
        "fields": [
            {
                "key": "housing_tenure",
                "label": "현재 거주형태",
                "type": "select",
                "required": True,
                "options": [
                    {"value":"OWNER_APARTMENT","label":"자가 (아파트)"},
                    {"value":"OWNER_OTHER","label":"자가 (빌라·단독·오피스텔)"},
                    {"value":"RENT","label":"전세 / 월세"},
                    {"value":"OTHER","label":"기타 (사택 등)"},
                ],
            },
            {
                "key": "housing_move_plan",
                "label": "노후 주거 이동 계획",
                "type": "select",
                "required": True,
                "options": [
                    {"value":"KEEP","label":"현재 주거지 유지"},
                    {"value":"DOWNSIZE","label":"평수 축소 (다운사이징)"},
                    {"value":"MOVE_LOWER_COST","label":"수도권 외곽·지방 이동"},
                    {"value":"SENIOR_RESIDENCE","label":"실버타운·시니어 레지던스"},
                ],
            },
            {
                "key": "reverse_mortgage_plan",
                "label": "주택연금 활용 계획",
                "type": "select",
                "required": True,
                "show_when_owner": True,
                "options": [
                    {"value":"PLAN_USE","label":"가입 예정"},
                    {"value":"CONSIDER_IF_NEEDED","label":"자금 부족 시 고려"},
                    {"value":"NO_PLAN","label":"활용 계획 없음"},
                    {"value":"UNKNOWN","label":"주택연금을 잘 모름"},
                ],
            },
            {
                "key": "reverse_mortgage_start_age",
                "label": "주택연금 가입 예정 나이",
                "type": "integer",
                "unit": "세",
                "min": 55,
                "max": 95,
                "required": True,
                "show_when": {"key":"reverse_mortgage_plan","value":"PLAN_USE"},
            },
        ],
    },
    "ACT_REVIEW_HEALTH_COVERAGE": {
        "question_id": "AWR_Q09_HEALTH_COVERAGE",
        "title": "보험·보장 점검하기",
        "description": "큰 병이 생겼을 때의 진단비·실손/입원 보장과 소득중단 대비 상태를 확인합니다. 보장 적정성 점수나 보험 추천은 만들지 않습니다.",
        "fields": [
            {
                "key": "critical_illness_benefit_band",
                "label": "3대 진단비(암·뇌·심장) 보장 일시금",
                "type": "select",
                "required": True,
                "options": [
                    {"value":"NONE_UNKNOWN","label":"없음 / 모름"},
                    {"value":"LT_30M","label":"3,000만 원 미만"},
                    {"value":"30M_60M","label":"3,000만 ~ 6,000만 원"},
                    {"value":"60M_100M","label":"6,000만 ~ 1억 원"},
                    {"value":"GE_100M","label":"1억 원 이상"},
                ],
            },
            {
                "key": "indemnity_coverage",
                "label": "실손·수술/입원 보험 준비",
                "type": "select",
                "required": True,
                "options": [
                    {"value":"NONE","label":"없음 / 미가입"},
                    {"value":"INDEMNITY_ONLY","label":"실손보험만 유지 중"},
                    {"value":"INDEMNITY_PLUS","label":"실손 + 수술·입원비 보장"},
                ],
            },
            {
                "key": "major_history",
                "label": "암·뇌·심혈관 본인 병력 또는 가족력",
                "type": "select",
                "required": True,
                "options": [
                    {"value":"NONE","label":"모두 해당 없음"},
                    {"value":"CANCER","label":"암 가족력 / 본인 병력"},
                    {"value":"VASCULAR","label":"뇌·심혈관 가족력 / 본인 병력"},
                    {"value":"BOTH","label":"암·혈관계 모두 해당"},
                ],
            },
            {
                "key": "income_stop_plan_checked",
                "label": "치료로 일을 쉬게 될 때 생활비 마련 방법을 확인했나요?",
                "type": "select",
                "required": True,
                "options": [
                    {"value":"YES","label":"예, 확인했습니다"},
                    {"value":"NO","label":"아직 확인하지 못했습니다"},
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
    "ACT_CREATE_EMERGENCY_DIGITAL_ASSET_LIST": {
        "question_id": "AWR_Q11_DIGITAL_FAMILY_INFO",
        "title": "가족 비상·디지털 자산 목록 만들기",
        "description": "비밀번호나 PIN을 저장하지 않고, 가족이 무엇이 있고 어디서 확인해야 하는지만 정리합니다.",
        "fields": [
            {
                "key": "digital_categories",
                "label": "목록에 포함한 항목",
                "type": "multi_select",
                "required": True,
                "options": [
                    {"value":"INSURANCE","label":"보험"},
                    {"value":"BANK_SECURITIES","label":"은행 · 증권계좌"},
                    {"value":"CRYPTO","label":"가상자산(코인)"},
                    {"value":"SIMPLE_PAY","label":"간편결제"},
                    {"value":"SUBSCRIPTIONS","label":"정기구독"},
                    {"value":"EMAIL_SOCIAL","label":"이메일 · SNS"},
                    {"value":"CLOUD_PHOTOS","label":"클라우드 · 사진"},
                ],
            },
            {
                "key": "inventory_location_type",
                "label": "목록 보관 위치 유형",
                "type": "select",
                "required": True,
                "options": [
                    {"value":"PHYSICAL_SECURE_FILE","label":"안전한 종이 문서 · 파일"},
                    {"value":"DIGITAL_SECURE_FILE","label":"안전한 디지털 문서"},
                    {"value":"TRUSTED_CONTACT","label":"신뢰하는 가족 · 담당자에게 위치 안내"},
                    {"value":"OTHER_SECURE_LOCATION","label":"그 밖의 안전한 보관 위치"},
                ],
            },
            {
                "key": "family_can_locate",
                "label": "가족이 그 목록의 위치를 알고 있나요?",
                "type": "select",
                "required": True,
                "options": [
                    {"value":"YES","label":"예"},
                    {"value":"NO","label":"아직 아니요"},
                ],
            },
            {
                "key": "access_procedure_prepared",
                "label": "필요할 때 확인할 절차를 정해두셨나요?",
                "type": "select",
                "required": True,
                "options": [
                    {"value":"YES","label":"예"},
                    {"value":"NO","label":"아직 아니요"},
                ],
            },
        ],
    },
    "ACT_START_FAMILY_WELLDYING_CONVERSATION": {
        "question_id": "AWR_Q12_WELLDYING_CONVERSATION",
        "title": "가족 대화 시작하기",
        "description": "가족과 실제로 한 번 이상 이야기하고, 최소 한 가지 선호사항을 기록하면 완료됩니다.",
        "fields": [
            {
                "key": "conversation_done",
                "label": "가족과 실제로 대화했나요?",
                "type": "select",
                "required": True,
                "options": [
                    {"value":"YES","label":"예, 이야기했습니다"},
                    {"value":"NO","label":"아직 못했습니다"},
                ],
            },
            {
                "key": "preference_topics",
                "label": "기록해 둔 선호사항",
                "type": "multi_select",
                "required": True,
                "options": [
                    {"value":"MEDICAL_DECISION","label":"의료 결정 · 연명의료"},
                    {"value":"CARE","label":"돌봄 방식"},
                    {"value":"ASSET_INHERITANCE","label":"재산 · 상속 의향"},
                    {"value":"FUNERAL_MEMORIAL","label":"장례 · 추모 방식"},
                    {"value":"DIGITAL_INFO","label":"디지털 자산 · 중요정보"},
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

def _multi_choice_field(fields: dict[str, Any], key: str, allowed: set[str]) -> list[str]:
    raw = fields.get(key)
    if not isinstance(raw, list) or not raw:
        raise ActionValidationError("REQUIRED", key)
    values=[]
    for item in raw:
        value=str(item)
        if value not in allowed:
            raise ActionValidationError("INVALID_CHOICE", key)
        if value not in values:
            values.append(value)
    return values

_SECRET_TERMS = (
    "password","passwd","passcode","pin","private_key","privatekey",
    "seed_phrase","seedphrase","mnemonic","recovery_phrase","recoveryphrase"
)

def reject_secret_fields(fields: dict[str, Any]) -> None:
    def walk(value: Any, path: str = "") -> None:
        if isinstance(value, dict):
            for k, v in value.items():
                key=str(k).lower().replace(" ","_").replace("-","_")
                if any(term in key for term in _SECRET_TERMS):
                    raise ActionValidationError("SECRET_NOT_ALLOWED", str(k))
                walk(v, f"{path}.{k}" if path else str(k))
        elif isinstance(value, list):
            for i, v in enumerate(value):
                walk(v, f"{path}[{i}]")
        elif isinstance(value, str):
            lower=value.lower()
            if any(term.replace("_"," ") in lower for term in _SECRET_TERMS if "_" in term):
                raise ActionValidationError("SECRET_NOT_ALLOWED", path or None)
    walk(fields)

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

def _fact_value(existing_facts: dict[str, Any], key: str) -> Any:
    item=existing_facts.get(key)
    if not isinstance(item, dict):
        return None
    if item.get("status") != "KNOWN":
        return None
    return item.get("value")

def income_gap_preview(existing_facts: dict[str, Any]) -> dict[str, Any]:
    retirement_age=_fact_value(existing_facts,"work.primary_job_exit_age")
    nps_start_age=_fact_value(existing_facts,"pension.nps.start_age_self")
    budget=_fact_value(existing_facts,"cashflow.retirement_monthly_budget_target")
    missing=[]
    if retirement_age is None:
        missing.append("ACT_CONFIRM_RETIREMENT_AGE")
    if nps_start_age is None:
        missing.append("ACT_CHECK_NPS_ESTIMATE")
    if budget is None:
        missing.append("ACT_ESTIMATE_RETIREMENT_BUDGET")
    if missing:
        return {"ready":False,"missing_actions":missing}
    years=max(0,int(nps_start_age)-int(retirement_age))
    return {
        "ready":True,
        "retirement_age":int(retirement_age),
        "nps_start_age_self":int(nps_start_age),
        "income_gap_years":years,
        "retirement_budget_10k":budget,
        "note":"월 부족액은 정밀 현금흐름 계산 전에는 만들지 않습니다.",
    }

def form_for(action_catalog_id: str, household_type: str) -> dict[str, Any]:
    if action_catalog_id not in ACTION_FORMS:
        raise ActionValidationError("ACTION_NOT_SUPPORTED")
    form = ACTION_FORMS[action_catalog_id]
    fields=[]
    for f in form["fields"]:
        x=dict(f)
        if x.get("required_when") == "household_type=couple":
            x["required"] = household_type == "couple"
        if x.get("show_when_owner"):
            x["show_when_owner"] = True
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
    existing_facts: dict[str, Any] | None = None,
) -> dict[str, Any]:
    existing_facts=existing_facts or {}
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

    if action_catalog_id == "ACT_CALCULATE_INCOME_GAP":
        preview=income_gap_preview(existing_facts)
        if not preview.get("ready"):
            raise ActionValidationError(
                "PRECONDITION_REQUIRED",
                ",".join(preview.get("missing_actions") or [])
            )
        bridge_sources=_multi_choice_field(fields,"bridge_sources",{
            "POST_RETIREMENT_WORK","RET_PRIVATE_PENSION","FINANCIAL_ASSETS","SPOUSE_INCOME","OTHER"
        })
        gap_years=int(preview["income_gap_years"])
        return {
            "question_id":"AWR_Q05_INCOME_GAP",
            "normalized":{
                "income_gap_years":gap_years,
                "bridge_sources":bridge_sources,
                "retirement_age":preview["retirement_age"],
                "nps_start_age_self":preview["nps_start_age_self"],
            },
            "facts":[
                {
                    "fact_key":"cashflow.income_gap_years_to_nps_self",
                    "status":"KNOWN",
                    "value":gap_years,
                    "unit":"years",
                    "source_type":"RULE_DERIVED",
                    "source_ref":"RULE_RETIREMENT_TO_NPS_START_V1",
                    "verification_level":"RULE_DERIVED",
                },
                {
                    "fact_key":"cashflow.income_gap_bridge_sources",
                    "status":"KNOWN",
                    "value":bridge_sources,
                    "unit":"source_list",
                    "source_type":"USER_CONFIRMED",
                    "source_ref":"ACT_CALCULATE_INCOME_GAP",
                    "verification_level":"SELF_REPORTED",
                },
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

    if action_catalog_id == "ACT_DEFINE_HOUSING_PLAN":
        tenure=_choice_field(fields,"housing_tenure",{
            "OWNER_APARTMENT","OWNER_OTHER","RENT","OTHER"
        })
        move=_choice_field(fields,"housing_move_plan",{
            "KEEP","DOWNSIZE","MOVE_LOWER_COST","SENIOR_RESIDENCE"
        })
        owner=tenure in {"OWNER_APARTMENT","OWNER_OTHER"}
        normalized={"housing_tenure":tenure,"housing_move_plan":move}
        facts=[
            {
                "fact_key":"housing.tenure_q16",
                "status":"KNOWN",
                "value":tenure,
                "unit":"Q16_choice",
                "source_type":"USER_CONFIRMED",
                "source_ref":"ACT_DEFINE_HOUSING_PLAN",
                "verification_level":"SELF_REPORTED",
            },
            {
                "fact_key":"housing.move_plan_q21",
                "status":"KNOWN",
                "value":move,
                "unit":"Q21_choice",
                "source_type":"USER_CONFIRMED",
                "source_ref":"ACT_DEFINE_HOUSING_PLAN",
                "verification_level":"SELF_REPORTED",
            },
        ]
        if owner:
            reverse=_choice_field(fields,"reverse_mortgage_plan",{
                "PLAN_USE","CONSIDER_IF_NEEDED","NO_PLAN","UNKNOWN"
            })
            normalized["reverse_mortgage_plan"]=reverse
            facts.append({
                "fact_key":"housing.reverse_mortgage_plan_q19",
                "status":"UNKNOWN" if reverse=="UNKNOWN" else "KNOWN",
                "value":reverse,
                "unit":"Q19_choice",
                "source_type":"USER_CONFIRMED",
                "source_ref":"ACT_DEFINE_HOUSING_PLAN",
                "verification_level":"SELF_REPORTED",
            })
            if reverse=="PLAN_USE":
                start_age=_int_field(fields,"reverse_mortgage_start_age",55,95)
                normalized["reverse_mortgage_start_age"]=start_age
                facts.append({
                    "fact_key":"housing.reverse_mortgage_start_age",
                    "status":"KNOWN",
                    "value":start_age,
                    "unit":"age_years",
                    "source_type":"USER_CONFIRMED",
                    "source_ref":"ACT_DEFINE_HOUSING_PLAN",
                    "verification_level":"SELF_REPORTED",
                })
        return {
            "question_id":"AWR_Q08_HOUSING",
            "normalized":normalized,
            "facts":facts,
        }

    if action_catalog_id == "ACT_REVIEW_HEALTH_COVERAGE":
        dx=_choice_field(fields,"critical_illness_benefit_band",{
            "NONE_UNKNOWN","LT_30M","30M_60M","60M_100M","GE_100M"
        })
        indemnity=_choice_field(fields,"indemnity_coverage",{
            "NONE","INDEMNITY_ONLY","INDEMNITY_PLUS"
        })
        history=_choice_field(fields,"major_history",{
            "NONE","CANCER","VASCULAR","BOTH"
        })
        income_stop=_choice_field(fields,"income_stop_plan_checked",{"YES","NO"})
        return {
            "question_id":"AWR_Q09_HEALTH_COVERAGE",
            "normalized":{
                "critical_illness_benefit_band":dx,
                "indemnity_coverage":indemnity,
                "major_history":history,
                "income_stop_plan_checked":income_stop=="YES",
            },
            "facts":[
                {
                    "fact_key":"health.critical_illness_benefit_band_q12",
                    "status":"UNKNOWN" if dx=="NONE_UNKNOWN" else "KNOWN",
                    "value":dx,
                    "unit":"Q12_band",
                    "source_type":"USER_CONFIRMED",
                    "source_ref":"ACT_REVIEW_HEALTH_COVERAGE",
                    "verification_level":"SELF_REPORTED",
                },
                {
                    "fact_key":"health.indemnity_coverage_q13",
                    "status":"KNOWN",
                    "value":indemnity,
                    "unit":"Q13_choice",
                    "source_type":"USER_CONFIRMED",
                    "source_ref":"ACT_REVIEW_HEALTH_COVERAGE",
                    "verification_level":"SELF_REPORTED",
                },
                {
                    "fact_key":"health.major_history_q11",
                    "status":"KNOWN",
                    "value":history,
                    "unit":"Q11_choice",
                    "source_type":"USER_CONFIRMED",
                    "source_ref":"ACT_REVIEW_HEALTH_COVERAGE",
                    "verification_level":"SELF_REPORTED",
                },
                {
                    "fact_key":"health.income_stop_plan_checked",
                    "status":"KNOWN",
                    "value":income_stop=="YES",
                    "unit":"boolean",
                    "source_type":"USER_CONFIRMED",
                    "source_ref":"ACT_REVIEW_HEALTH_COVERAGE",
                    "verification_level":"SELF_REPORTED",
                },
            ],
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

    if action_catalog_id == "ACT_CREATE_EMERGENCY_DIGITAL_ASSET_LIST":
        categories=_multi_choice_field(fields,"digital_categories",{
            "INSURANCE","BANK_SECURITIES","CRYPTO","SIMPLE_PAY",
            "SUBSCRIPTIONS","EMAIL_SOCIAL","CLOUD_PHOTOS"
        })
        location=_choice_field(fields,"inventory_location_type",{
            "PHYSICAL_SECURE_FILE","DIGITAL_SECURE_FILE",
            "TRUSTED_CONTACT","OTHER_SECURE_LOCATION"
        })
        locatable=_choice_field(fields,"family_can_locate",{"YES","NO"})
        procedure=_choice_field(fields,"access_procedure_prepared",{"YES","NO"})
        if locatable!="YES":
            raise ActionValidationError("COMPLETION_CRITERIA_NOT_MET","family_can_locate")
        if procedure!="YES":
            raise ActionValidationError("COMPLETION_CRITERIA_NOT_MET","access_procedure_prepared")
        return {
            "question_id":"AWR_Q11_DIGITAL_FAMILY_INFO",
            "normalized":{
                "digital_categories":categories,
                "inventory_location_type":location,
                "family_can_locate":True,
                "access_procedure_prepared":True,
            },
            "facts":[
                {
                    "fact_key":"digital_legacy.inventory_categories",
                    "status":"KNOWN",
                    "value":categories,
                    "unit":"category_list",
                    "source_type":"USER_CONFIRMED",
                    "source_ref":"ACT_CREATE_EMERGENCY_DIGITAL_ASSET_LIST",
                    "verification_level":"SELF_REPORTED",
                },
                {
                    "fact_key":"digital_legacy.inventory_location_type",
                    "status":"KNOWN",
                    "value":location,
                    "unit":"location_type",
                    "source_type":"USER_CONFIRMED",
                    "source_ref":"ACT_CREATE_EMERGENCY_DIGITAL_ASSET_LIST",
                    "verification_level":"SELF_REPORTED",
                },
                {
                    "fact_key":"digital_legacy.family_can_locate",
                    "status":"KNOWN",
                    "value":True,
                    "unit":"boolean",
                    "source_type":"USER_CONFIRMED",
                    "source_ref":"ACT_CREATE_EMERGENCY_DIGITAL_ASSET_LIST",
                    "verification_level":"SELF_REPORTED",
                },
                {
                    "fact_key":"digital_legacy.access_procedure_prepared",
                    "status":"KNOWN",
                    "value":True,
                    "unit":"boolean",
                    "source_type":"USER_CONFIRMED",
                    "source_ref":"ACT_CREATE_EMERGENCY_DIGITAL_ASSET_LIST",
                    "verification_level":"SELF_REPORTED",
                },
            ],
        }

    if action_catalog_id == "ACT_START_FAMILY_WELLDYING_CONVERSATION":
        conversation=_choice_field(fields,"conversation_done",{"YES","NO"})
        topics=_multi_choice_field(fields,"preference_topics",{
            "MEDICAL_DECISION","CARE","ASSET_INHERITANCE","FUNERAL_MEMORIAL","DIGITAL_INFO"
        })
        if conversation!="YES":
            raise ActionValidationError("COMPLETION_CRITERIA_NOT_MET","conversation_done")
        return {
            "question_id":"AWR_Q12_WELLDYING_CONVERSATION",
            "normalized":{
                "conversation_done":True,
                "preference_topics":topics,
            },
            "facts":[
                {
                    "fact_key":"welldying.family_conversation_done",
                    "status":"KNOWN",
                    "value":True,
                    "unit":"boolean",
                    "source_type":"USER_CONFIRMED",
                    "source_ref":"ACT_START_FAMILY_WELLDYING_CONVERSATION",
                    "verification_level":"SELF_REPORTED",
                },
                {
                    "fact_key":"welldying.preference_topics_recorded",
                    "status":"KNOWN",
                    "value":topics,
                    "unit":"topic_list",
                    "source_type":"USER_CONFIRMED",
                    "source_ref":"ACT_START_FAMILY_WELLDYING_CONVERSATION",
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
