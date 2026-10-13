"""Anonymous preparation preview. No FACT writes or precision-engine estimates.

Months are explicitly reported by the user, never inferred from age/birth year.
The only derived number is a calendar interval; UNKNOWN amounts stay null.
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Annotated, Literal
from zoneinfo import ZoneInfo
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, model_validator

VERSION = "INCOME_GAP_PREPARATION_V1"
WORKSHEETS = {
    "RETIREMENT": ["퇴직 예상 월 / 확인한 담당자·자료", "마지막 급여 입금 월 / 퇴직금 입금 시점은 별도 확인", "다음 확인 날짜"],
    "NPS": ["조회 기준일 / 본인·배우자 구분", "조회한 수령 시작 월 / 월 예상액(만원)", "미확인 항목 / 추가 확인할 곳"],
    "BUDGET": ["주거·식비·교통·의료·보험·기타 월 지출", "월 대출 상환액 / 생활비 포함 여부", "퇴직 후 줄어들 항목 / 추가될 항목"],
    "PRIVATE_PENSION": ["연금 종류·금융회사(계좌번호 제외)", "수령 시작 월 / 월 예상액 / 지급 종료·기간", "확인 자료·기준일 / 모르는 항목"],
    "ASSETS": ["사용할 수 있는 금융자산 구간 / 확인 기준일", "큰 지출 종류 / 시점 / 확인한 금액 또는 미확인", "부채 잔액과 월 상환액을 각각 기록"],
    "WORK": ["희망하는 일 / 시작 시점 / 예상 기간", "예상 월 소득 / 확정인지 계획인지", "기관·담당자에게 확인할 조건 / 다음 확인일"],
    "BRIDGE": ["월급 종료~연금 시작의 기간별 수입·지출 목록", "확인한 정보 / 아직 모르는 정보", "사용할 자산·큰 지출 / 정밀 계산에서 확인할 질문"],
    "ALTERNATIVE_INCOME": ["국민연금 수급 계획이 없는 이유 / 확인 근거", "다른 연금·일·자산에서 조달할 수입과 기간", "목표 생활비 / 추가로 확인할 정보"],
    "DISCUSSION": ["누구와 언제 실제로 이야기했나요?", "합의한 이번 달 행동 / 담당 / 목표일", "다음에 다시 확인할 날짜"],
}
Month = Annotated[str, Field(pattern=r"^(20\d{2}|2100)-(0[1-9]|1[0-2])$")]
Money = Annotated[float, Field(strict=True, ge=0, le=1000000, allow_inf_nan=False)]
State = Literal["UNKNOWN", "CONFIRMED", "NONE"]


class ClosedModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Pension(ClosedModel):
    state: State = "UNKNOWN"
    start_month: Month | None = None
    monthly_10k: Money | None = None

    @model_validator(mode="after")
    def consistent(self):
        if self.state != "CONFIRMED" and (self.start_month is not None or self.monthly_10k is not None):
            raise ValueError("확인하지 않은 연금에 시점이나 금액을 입력할 수 없습니다.")
        return self


class Work(ClosedModel):
    state: Literal["UNKNOWN", "NONE", "PLAN_ONLY", "CONFIRMED"] = "UNKNOWN"
    monthly_10k: Money | None = None

    @model_validator(mode="after")
    def consistent(self):
        if self.state in ("UNKNOWN", "NONE") and self.monthly_10k is not None:
            raise ValueError("확인하지 않은 소득에 금액을 입력할 수 없습니다.")
        return self


class IncomeGapInput(ClosedModel):
    household: Literal["UNKNOWN", "single", "couple"] = "UNKNOWN"
    job_exit_month: Month | None = None
    last_salary_month: Month | None = None
    budget_monthly_10k: Money | None = None
    debt_monthly_10k: Money | None = None
    debt_in_budget: Literal["UNKNOWN", "YES", "NO"] = "UNKNOWN"
    nps_self: Pension = Field(default_factory=Pension)
    nps_spouse: Pension = Field(default_factory=Pension)
    private_pension: Pension = Field(default_factory=Pension)
    post_work: Work = Field(default_factory=Work)
    liquid_assets_band: Literal["UNKNOWN", "UNDER_1000", "1000_5000", "5000_10000", "OVER_10000"] = "UNKNOWN"
    large_cost_state: Literal["UNKNOWN", "NONE", "PLANNED"] = "UNKNOWN"
    family_discussion: Literal["UNKNOWN", "NOT_YET", "DONE"] = "UNKNOWN"
    bridge_methods: list[Literal["LIQUID_ASSETS", "PRIVATE_PENSION", "WORK", "REDUCE_SPENDING", "OTHER_CONFIRM"]] = Field(default_factory=list, max_length=5)

    @model_validator(mode="after")
    def unique_methods(self):
        if len(set(self.bridge_methods)) != len(self.bridge_methods):
            raise ValueError("연결 방법을 중복 선택할 수 없습니다.")
        return self


def _f(key, label, kind="select", options=None, **kw):
    f = {"key": key, "label": label, "type": kind, **kw}
    if options is not None:
        f["options"] = [{"value": v, "label": text} for v, text in options]
    return f


def _pension_fields(key):
    return [
        _f(f"{key}.state", "예상 수령 정보 확인", options=[("UNKNOWN", "아직 잘 모릅니다"), ("CONFIRMED", "확인한 정보가 있습니다"), ("NONE", "현재 받을 연금이 없음을 확인했습니다")]),
        _f(f"{key}.start_month", "조회하거나 확인한 수령 시작 월", "month", show_when={"key": f"{key}.state", "value": "CONFIRMED"}),
        _f(f"{key}.monthly_10k", "조회하거나 확인한 월 예상액", "money", unit="만원/월", show_when={"key": f"{key}.state", "value": "CONFIRMED"}),
    ]


def questions():
    return {"version": VERSION, "total": 12, "questions": [
        {"id": "G01", "title": "생활비를 함께 준비하는 배우자가 있나요?", "fields": [_f("household", "가구 형태", options=[("UNKNOWN", "아직 선택하지 않았습니다"), ("single", "배우자 없이 준비합니다"), ("couple", "배우자와 함께 준비합니다")])]},
        {"id": "G02", "title": "현재 직장을 언제 그만둘 예정인가요?", "fields": [_f("job_exit_month", "퇴직 예상 월", "month")]},
        {"id": "G03", "title": "현재 직장의 마지막 월급은 언제 들어오나요?", "hint": "퇴직 월과 마지막 급여가 입금되는 월은 다를 수 있습니다. 다음 달을 월급이 없는 첫 달로 표시합니다.", "fields": [_f("last_salary_month", "마지막 월급 입금 월", "month")]},
        {"id": "G04", "title": "퇴직 후 매달 필요한 생활비는 얼마인가요?", "fields": [_f("budget_monthly_10k", "가구 목표 월 생활비", "money", unit="만원/월")]},
        {"id": "G05", "title": "매달 갚을 대출과 생활비에 포함했는지 확인했나요?", "hint": "대출이 없음을 확인했다면 0을 입력하세요. 모르는 금액은 비워두세요.", "fields": [_f("debt_monthly_10k", "월 대출 상환액", "money", unit="만원/월"), _f("debt_in_budget", "목표 생활비에 상환액을 포함했나요?", options=[("UNKNOWN", "아직 확인하지 않았습니다"), ("YES", "포함했습니다"), ("NO", "포함하지 않았습니다")])]},
        {"id": "G06", "title": "본인 국민연금의 시작 월과 예상액을 확인했나요?", "fields": _pension_fields("nps_self")},
        {"id": "G07", "title": "배우자 국민연금도 각각 확인했나요?", "show_when": {"key": "household", "value": "couple"}, "fields": _pension_fields("nps_spouse")},
        {"id": "G08", "title": "퇴직·개인연금의 수령 계획을 확인했나요?", "hint": "여러 연금의 기간이 다르면 합쳐 입력하지 마세요. 이 단계에서는 대표 계획만 기록하고 상세 지급 기간은 별도 확인합니다.", "fields": _pension_fields("private_pension")},
        {"id": "G09", "title": "퇴직 후 일할 소득은 확정됐나요, 계획인가요?", "hint": "계획 중인 소득과 확정한 소득을 구분합니다. 이 미리보기는 재취업 소득을 자동 합산하지 않습니다.", "fields": [_f("post_work.state", "일·소득 준비 상태", options=[("UNKNOWN", "아직 모릅니다"), ("NONE", "현재 계획이 없습니다"), ("PLAN_ONLY", "계획만 있습니다"), ("CONFIRMED", "확인한 일·소득이 있습니다")]), _f("post_work.monthly_10k", "예상 월 소득", "money", unit="만원/월", show_when_any={"key": "post_work.state", "values": ["PLAN_ONLY", "CONFIRMED"]})]},
        {"id": "G10", "title": "생활비로 쓸 수 있는 금융자산 구간을 알고 있나요?", "hint": "집값이나 당장 쓸 수 없는 퇴직금은 제외합니다. 구간에서 정확한 금액을 만들지 않습니다.", "fields": [_f("liquid_assets_band", "사용 가능한 금융자산", options=[("UNKNOWN", "아직 모릅니다"), ("UNDER_1000", "1,000만원 미만"), ("1000_5000", "1,000만원 이상~5,000만원 미만"), ("5000_10000", "5,000만원 이상~1억원 미만"), ("OVER_10000", "1억원 이상")])]},
        {"id": "G11", "title": "자녀 지원·이사 등 큰 지출을 확인했나요?", "fields": [_f("large_cost_state", "예정된 큰 지출", options=[("UNKNOWN", "아직 확인하지 않았습니다"), ("NONE", "현재 예정된 지출이 없음을 확인했습니다"), ("PLANNED", "예정된 큰 지출이 있습니다")])]},
        {"id": "G12", "title": "이 계획을 가족이나 신뢰하는 사람과 이야기했나요?", "fields": [_f("family_discussion", "실제 대화 여부", options=[("UNKNOWN", "아직 선택하지 않았습니다"), ("NOT_YET", "아직 이야기하지 않았습니다"), ("DONE", "실제로 이야기했습니다")])]},
    ]}


def _month_index(month):
    year, number = map(int, month.split("-"))
    return year * 12 + number - 1


def _next_month(month):
    year, number = divmod(_month_index(month) + 1, 12)
    return f"{year:04d}-{number + 1:02d}"


def build_preview(payload: IncomeGapInput, today: date | None = None):
    today = today or datetime.now(ZoneInfo("Asia/Seoul")).date()
    data = payload.model_dump()
    if payload.household != "couple":
        data["nps_spouse"] = Pension().model_dump()
    missing = []
    candidates = []

    def action(code, catalog, title, reason, days, steps, completion, support):
        candidates.append({"code": code, "action_catalog_id": catalog, "title": title, "reason": reason,
                           "target_date": (today + timedelta(days=days)).isoformat(), "steps": steps,
                           "completion": completion, "support": support, "worksheet": WORKSHEETS[code], "status": "TO_VERIFY"})

    salary_free = _next_month(payload.last_salary_month) if payload.last_salary_month else None
    own = data["nps_self"]
    start = own["start_month"] if own["state"] == "CONFIRMED" else None
    gap = max(0, _month_index(start) - _month_index(salary_free)) if salary_free and start else None
    spouse = data["nps_spouse"]
    spouse_start = spouse["start_month"] if spouse["state"] == "CONFIRMED" else None
    both = max(start, spouse_start) if start and spouse_start and payload.household == "couple" else None

    if payload.household == "UNKNOWN":
        missing.append({"key": "household", "label": "생활비를 함께 준비할 가구 범위"})
    if payload.household == "UNKNOWN" or not payload.job_exit_month or not salary_free:
        for key, label in [("job_exit_month", "퇴직 예상 월"), ("last_salary_month", "마지막 월급 입금 월")]:
            if data[key] is None:
                missing.append({"key": key, "label": label})
        action("RETIREMENT", "ACT_CONFIRM_RETIREMENT_AGE", "가구 범위·퇴직·마지막 급여 시점 확인하기", "함께 준비할 범위와 월급이 없는 첫 달을 먼저 정해야 합니다.", 7,
               ["생활비를 함께 준비할 가구 범위를 확인합니다.", "회사 인사 담당자에게 퇴직 예상 월을 확인합니다.", "마지막 급여 입금 월을 별도로 확인합니다."], "가구 범위와 두 시점·확인 근거를 기록합니다.", "인사 담당자에게 물을 질문 목록을 제공합니다.")

    pension_missing = []
    for who, label in [("nps_self", "본인"), ("nps_spouse", "배우자")]:
        if who == "nps_spouse" and payload.household != "couple":
            continue
        p = data[who]
        if p["state"] == "NONE":
            continue
        for key, description in [("start_month", "시작 월"), ("monthly_10k", "월 예상액")]:
            if p[key] is None:
                missing.append({"key": f"{who}.{key}", "label": f"{label} 국민연금 {description}"})
                pension_missing.append(label)
    if pension_missing:
        action("NPS", "ACT_CHECK_NPS_ESTIMATE", "국민연금 시작 월·예상액 확인하기", "확인되지 않은 연금은 0원으로 보지 않습니다.", 7,
               ["공식 국민연금 조회에서 본인 정보를 확인합니다.", "배우자가 있다면 배우자 정보도 별도로 확인합니다.", "조회 기준일·시작 월·월 예상액을 기록합니다."], "각자의 확인한 정보 또는 수급 계획이 없는 이유를 기록합니다.", "공식 조회에서 확인할 항목을 정리해 드립니다.")

    if payload.budget_monthly_10k is None or payload.debt_monthly_10k is None or payload.debt_in_budget == "UNKNOWN" or (payload.debt_monthly_10k > 0 and payload.debt_in_budget == "NO"):
        for key, label in [("budget_monthly_10k", "목표 월 생활비"), ("debt_monthly_10k", "월 대출 상환액")]:
            if data[key] is None:
                missing.append({"key": key, "label": label})
        if payload.debt_in_budget == "UNKNOWN":
            missing.append({"key": "debt_in_budget", "label": "생활비의 대출 상환액 포함 여부"})
        action("BUDGET", "ACT_ESTIMATE_RETIREMENT_BUDGET", "퇴직 후 생활비·대출 상환액 정리하기", "상환액 포함 여부를 확인해야 지출을 빠뜨리거나 두 번 세지 않습니다.", 14,
               ["최근 지출에서 퇴직 후에도 필요한 항목을 정리합니다.", "대출 상환액과 생활비 포함 여부를 확인합니다."], "목표 생활비와 상환액 포함 여부를 기록합니다.", "생활비 항목별 정리표를 제공합니다.")

    if data["private_pension"]["state"] == "UNKNOWN" or (data["private_pension"]["state"] == "CONFIRMED" and (data["private_pension"]["start_month"] is None or data["private_pension"]["monthly_10k"] is None)):
        missing.append({"key": "private_pension", "label": "퇴직·개인연금 수령 정보"})
        action("PRIVATE_PENSION", "ACT_CHECK_RET_PRIVATE_PENSION", "퇴직·개인연금 지급 계획 확인하기", "수령 시작·금액·지급 기간은 각각 확인해야 합니다.", 14,
               ["가입 금융회사에서 지급 시작·월 금액·지급 기간을 확인합니다.", "여러 연금은 각각 정리합니다."], "연금별 지급 정보 또는 가입하지 않았음을 확인합니다.", "연금별 확인 항목 정리표를 제공합니다.")

    if payload.liquid_assets_band == "UNKNOWN" or payload.large_cost_state in ("UNKNOWN", "PLANNED"):
        for key, label in [("liquid_assets_band", "사용 가능한 금융자산 구간"), ("large_cost_state", "예정된 큰 지출")]:
            if data[key] == "UNKNOWN":
                missing.append({"key": key, "label": label})
        action("ASSETS", "ACT_SUMMARIZE_ASSETS_DEBT", "사용할 자산·큰 지출 정리하기", "자산 구간을 임의의 정확한 금액으로 바꾸지 않습니다.", 14,
               ["금융자산 중 실제 사용할 수 있는 범위를 확인합니다.", "자녀 지원·이사 등 큰 지출의 시점과 금액을 별도로 정리합니다."], "확인한 자산 구간과 큰 지출 목록을 기록합니다.", "자산·지출 목록 양식을 제공합니다.")

    if payload.post_work.state in ("UNKNOWN", "PLAN_ONLY") or (payload.post_work.state == "CONFIRMED" and payload.post_work.monthly_10k is None):
        if payload.post_work.state == "UNKNOWN" or payload.post_work.monthly_10k is None:
            missing.append({"key": "post_work", "label": "퇴직 후 일·소득의 확인 상태"})
        action("WORK", "ACT_DEFINE_POST_RETIREMENT_WORK", "퇴직 후 일 계획의 조건 확인하기", "계획 중인 소득은 확정한 수입으로 합산하지 않습니다.", 30,
               ["가능한 일과 시작 시점·기간을 확인합니다.", "예상 소득과 확정 여부를 구분해 기록합니다."], "일 계획의 조건과 확인 여부를 기록합니다.", "일자리 기관에 확인할 질문 목록을 제공합니다. 취업은 보장하지 않습니다.")

    if payload.household != "UNKNOWN" and payload.job_exit_month and salary_free and start and own["monthly_10k"] is not None and payload.budget_monthly_10k is not None and gap > 0:
        action("BRIDGE", "ACT_CALCULATE_INCOME_GAP", "월급 종료부터 연금 시작까지 준비 계획 세우기", f"국민연금 시작 전 {gap}개월의 생활비 조달 방법을 확인합니다.", 30,
               ["기간별로 실제 받을 수입과 필요한 지출을 확인합니다.", "사용할 금융자산과 큰 지출을 함께 정리합니다.", "확인되지 않은 수입을 제외한 정밀 계산을 요청합니다."], "기간별 조달 계획과 아직 확인할 항목을 기록합니다.", "소득공백 달력과 확인 항목을 제공합니다. 월 부족액·총 필요자금은 이 단계에서 계산하지 않습니다.")

    if own["state"] == "NONE":
        action("ALTERNATIVE_INCOME", None, "국민연금 외 생활비 조달 계획 확인하기", "현재 국민연금 수급 계획이 없으므로 다른 수입과 조달 기간을 확인합니다.", 30,
               ["국민연금 수급 계획이 없는 이유와 확인 근거를 정리합니다.", "다른 연금·일·사용 가능한 자산으로 준비할 방법과 기간을 확인합니다."], "확인한 다른 수입·조달 방법과 미확인 항목을 기록합니다.", "대체 수입과 목표 생활비를 나란히 확인할 정리 항목을 제공합니다. 연금 자격을 판단하지 않습니다.")

    if payload.family_discussion != "DONE":
        action("DISCUSSION", None, "준비 계획을 가족·신뢰하는 사람과 이야기하기", "퇴직 시점·생활비·이번 달 행동을 함께 확인합니다.", 30,
               ["확인한 달력과 모르는 항목을 공유합니다.", "이번 달 행동과 담당·목표일을 합의합니다."], "실제 대화 후 합의한 행동과 목표일을 기록합니다.", "생활비·퇴직 준비 대화 질문을 제공합니다. 웰다잉 Action 완료로 처리하지 않습니다.")

    # Missing prerequisite actions precede downstream review actions. Stable order,
    # no scores, probabilities, or AI-generated facts.
    return {
        "version": VERSION, "as_of": today.isoformat(), "role": "PREPARATION_PREVIEW",
        "persistence": "NONE", "fact_writes": False, "answers": data,
        "calendar": {"last_salary_month": payload.last_salary_month, "first_salary_free_month": salary_free,
                     "nps_self_state": own["state"], "nps_spouse_state": spouse["state"],
                     "nps_self_start_month": start, "nps_spouse_start_month": spouse_start if payload.household == "couple" else None,
                     "both_nps_started_month": both, "nps_wait_months": gap,
                     "status": "RULE_DERIVED" if gap is not None else "UNKNOWN",
                     "source_refs": ["last_salary_month", "nps_self.start_month"] if gap is not None else []},
        "monthly_shortfall_10k": None, "total_bridge_need_10k": None,
        "missing": missing, "top3": candidates[:3],
        "notes": ["입력한 값 중 확인한 정보만 달력에 반영합니다.",
                  "연금 시작 전 기간은 무소득 기간이라는 뜻이 아닙니다. 다른 수입은 별도로 확인해야 합니다.",
                  "월 부족액·총 필요자금·자산 소진 나이·연금 자격은 계산하지 않습니다.",
                  "이 결과는 서버나 MY LIFE에 저장하지 않습니다. 회원 Action의 확인 완료와는 별개입니다."]
    }
