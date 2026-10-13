"""Member review contracts. Explicit user review -> scoped FACT -> focused plan.

No age/month conversion, precision estimates, or legacy Awareness completion.
"""
import hashlib
import json
from copy import deepcopy
from typing import Literal
from uuid import UUID
from pydantic import Field, model_validator
from .income_gap import ClosedModel, IncomeGapInput, build_preview, questions

GROUPS = {
    "RETIREMENT": {"title": "퇴직·마지막 급여 시점 확인", "keys": ["household", "job_exit_month", "last_salary_month"], "questions": [0, 1, 2]},
    "NPS": {"title": "본인·배우자 국민연금 확인", "keys": ["nps_self", "nps_spouse"], "questions": [5, 6]},
    "BUDGET": {"title": "생활비·대출 상환액 확인", "keys": ["budget_monthly_10k", "debt_monthly_10k", "debt_in_budget"], "questions": [3, 4]},
    "BRIDGE": {"title": "소득공백 연결 계획 확인", "keys": ["bridge_methods"], "questions": []},
    "PRIVATE_PENSION": {"title": "퇴직·개인연금 지급 계획 확인", "keys": ["private_pension"], "questions": [7]},
    "ASSETS": {"title": "사용 가능한 자산·큰 지출 확인", "keys": ["liquid_assets_band", "large_cost_state"], "questions": [9, 10]},
    "WORK": {"title": "퇴직 후 일·소득 조건 확인", "keys": ["post_work"], "questions": [8]},
}
METHODS = [("LIQUID_ASSETS", "사용 가능한 금융자산"), ("PRIVATE_PENSION", "퇴직·개인연금 계획"), ("WORK", "퇴직 후 일 계획"), ("REDUCE_SPENDING", "지출 조정"), ("OTHER_CONFIRM", "다른 방법을 추가 확인")]


class GapReviewRequest(ClosedModel):
    group: Literal["RETIREMENT", "NPS", "BUDGET", "BRIDGE", "PRIVATE_PENSION", "ASSETS", "WORK"]
    answers: IncomeGapInput
    acknowledged: bool = Field(strict=True)
    expected_revision: int = Field(strict=True, ge=0)
    request_id: UUID

    @model_validator(mode="after")
    def explicit_review(self):
        if not self.acknowledged:
            raise ValueError("입력과 미확인 항목을 검토했다는 확인이 필요합니다.")
        return self


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def signature(answers, group):
    keys = list(GROUPS[group]["keys"])
    if group in ("NPS", "BUDGET"):
        keys.append("household")
    if group == "BRIDGE":
        keys += GROUPS["RETIREMENT"]["keys"] + GROUPS["NPS"]["keys"] + GROUPS["BUDGET"]["keys"]
    values = {k: answers.get(k) for k in keys}
    if group == "BRIDGE":
        defaults = IncomeGapInput().model_dump()
        for key in ("private_pension", "liquid_assets_band", "large_cost_state", "post_work"):
            if answers.get(key, defaults[key]) != defaults[key]:
                values[key] = answers[key]
    return digest(values)


def states(record):
    result = {}
    for group in GROUPS:
        confirmed = record.get("confirmations", {}).get(group)
        result[group] = (confirmed["status"] if confirmed["digest"] == signature(record["answers"], group) else "REVIEW_DUE") if confirmed else "UNREVIEWED"
    return result


def enrich(record, result):
    status = states(record)
    catalog = questions()["questions"]
    reviews = []
    for group, meta in GROUPS.items():
        fields = []
        for i in meta["questions"]:
            q = catalog[i]
            for field in q["fields"]:
                f = deepcopy(field)
                if q.get("show_when"):
                    f["household_only"] = "couple"
                fields.append(f)
        if group == "BRIDGE":
            fields = [{"key": "bridge_methods", "label": "검토한 연결 방법 (수입이 확정됐다는 뜻은 아닙니다)", "type": "multi_select", "options": [{"value": value, "label": label} for value, label in METHODS]}]
        ready = group != "BRIDGE" or all(status[k] == "DONE" for k in ("RETIREMENT", "NPS", "BUDGET"))
        reviews.append({"group": group, "title": meta["title"], "status": status[group], "ready": ready, "fields": fields})
    pending = []
    for review in reviews:
        if review["status"] != "DONE" and review["ready"]:
            pending.append({"code": review["group"], "action_catalog_id": f"GAP_V1_{review['group']}", "title": review["title"],
                            "reason": "저장한 초안의 정보와 아직 모르는 항목을 검토합니다.", "target_date": result["as_of"],
                            "steps": ["확인한 값은 수정하고, 모르는 값은 비워 둡니다.", "검토 확인 후 저장합니다. 미확인 정보가 있으면 부분 확인으로 남습니다."],
                            "completion": "필수 정보와 적용 여부가 확인되어야 확인 완료입니다.", "support": "입력값과 검토 항목을 함께 표시합니다."})
    # Existing follow-ups remain after scoped reviews. Completed bridge is removed.
    for action in result["top3"]:
        if action["code"] not in GROUPS:
            pending.append(action)
    result.update(revision=record.get("revision", 0), reviews=reviews, top3=pending[:3],
                  reviewed_groups=sum(v == "DONE" for v in status.values()), review_total=len(GROUPS))
    result["notes"][-1] = "저장한 초안 전체가 자동 FACT가 되지는 않습니다. 검토 후 저장한 항목만 자기확인 FACT로 기록하며 기존 12영역 확인 완료와 구분합니다."
    return result


def prepare(record, payload: GapReviewRequest):
    group = payload.group
    raw = payload.answers.model_dump()
    request_hash = digest({"group": group, "answers": raw, "expected_revision": payload.expected_revision})
    patch = {k: deepcopy(raw[k]) for k in GROUPS[group]["keys"]}
    merged = {**deepcopy(record["answers"]), **patch}
    merged = build_preview(IncomeGapInput(**merged))["answers"]
    if group == "BRIDGE" and not all(states(record)[k] == "DONE" for k in ("RETIREMENT", "NPS", "BUDGET")):
        from .store import StoreError
        raise StoreError("GAP_PREREQUISITES_REQUIRED", 409)
    fact_rows = []
    prefix = f"gap.v1.{record['preparation_id']}."
    source_ref = f"GAP_REVIEW:{record['preparation_id']}:{group}"

    def fact(key, value, *, not_applicable=False, derived=False, unit=None):
        missing = value is None or value == "UNKNOWN" or value == []
        fact_rows.append({"fact_key": prefix + key, "value": None if missing or not_applicable else value,
                          "status": "NOT_APPLICABLE" if not_applicable else "UNKNOWN" if missing else "KNOWN",
                          "source_type": "RULE_DERIVED" if derived else "USER_CONFIRMED", "source_ref": source_ref,
                          "verification_level": "SELF_REPORTED", "unit": unit})

    if group == "RETIREMENT":
        for key in GROUPS[group]["keys"]:
            fact(key, merged[key], unit="MONTH" if key.endswith("month") else None)
    elif group == "NPS":
        for who in ("nps_self", "nps_spouse"):
            p = merged[who]
            excluded = who == "nps_spouse" and merged["household"] == "single"
            fact(f"{who}.state", p["state"], not_applicable=excluded)
            for key, unit in (("start_month", "MONTH"), ("monthly_10k", "만원/월")):
                fact(f"{who}.{key}", p[key], not_applicable=excluded or p["state"] == "NONE", unit=unit)
        fact("nps_household_scope", merged["household"])
    elif group == "BUDGET":
        for key in GROUPS[group]["keys"]:
            fact(key, merged[key], unit="만원/월" if key.endswith("10k") else None)
        fact("budget_household_scope", merged["household"])
    elif group == "PRIVATE_PENSION":
        pension = merged["private_pension"]
        fact("private_pension.state", pension["state"])
        for key, unit in (("start_month", "MONTH"), ("monthly_10k", "만원/월")):
            fact(f"private_pension.{key}", pension[key], not_applicable=pension["state"] == "NONE", unit=unit)
    elif group == "ASSETS":
        fact("liquid_assets_band", merged["liquid_assets_band"], unit="BAND_만원")
        fact("large_cost_state", merged["large_cost_state"])
    elif group == "WORK":
        work = merged["post_work"]
        fact("post_work.state", work["state"])
        fact("post_work.monthly_10k", work["monthly_10k"], not_applicable=work["state"] == "NONE", unit="만원/월")
    else:
        interval = build_preview(IncomeGapInput(**merged))["calendar"]["nps_wait_months"]
        fact("nps_wait_months", interval, not_applicable=merged["nps_self"]["state"]=="NONE", derived=True, unit="MONTH")
        fact("bridge_methods", merged["bridge_methods"], not_applicable=interval == 0)
    status = "DONE" if all(f["status"] in ("KNOWN", "NOT_APPLICABLE") for f in fact_rows) else "PARTIAL"
    if group == "BUDGET" and merged["debt_monthly_10k"] and merged["debt_in_budget"] == "NO":
        status = "PARTIAL"
    if group == "WORK" and merged["post_work"]["state"] == "PLAN_ONLY":
        status = "PARTIAL"
    if group == "ASSETS" and merged["large_cost_state"] == "PLANNED":
        status = "PARTIAL"
    fingerprint = signature(merged, group)
    future = {**deepcopy(record), "answers": merged, "revision": record.get("revision", 0) + 1}
    future.setdefault("confirmations", {})[group] = {"status": status, "digest": fingerprint}
    invalidated = [k for k, info in record.get("confirmations", {}).items() if k != group and info["digest"] != signature(merged, k)]
    before = enrich(record, build_preview(IncomeGapInput(**record["answers"])))
    after = enrich(future, build_preview(IncomeGapInput(**merged)))
    return {"answers": merged, "facts": fact_rows, "status": status, "digest": fingerprint, "request_hash": request_hash, "invalidated_groups": invalidated,
            "top3_before": [a["code"] for a in before["top3"]], "top3_after": [a["code"] for a in after["top3"]]}
