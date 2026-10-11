"""Opt-in live dev API checks; leaves synthetic data on a disposable account.

Supply LIFE2_E2E_ACCESS_TOKEN through a secure environment, never a command argument.
Set LIFE2_E2E_DISPOSABLE_ACCOUNT=1 only for a fresh, dedicated test member.
An optional LIFE2_E2E_ISOLATION_ACCESS_TOKEN enables second-member isolation checks.
Both members must be fresh test accounts. This does not test browser login, signup UI or PDF.
"""
import os
import sys

import httpx

BASE_URL = "https://life2-api-dev.onrender.com"


class VerificationError(Exception):
    pass


def require(condition, message):
    if not condition:
        raise VerificationError(message)


def request(client, method, path, **kwargs):
    response = client.request(method, path, **kwargs)
    # Do not print response bodies, identifiers, credentials or personal data.
    require(response.is_success, f"HTTP {response.status_code}: {method} API request")
    body = response.json()
    require(body.get("ok") is True, "API response did not report success")
    return body.get("data", body)


def top3_ids(dashboard):
    return [item["action_catalog_id"] for item in dashboard.get("top3", [])]


def require_empty_member(facts, dashboard):
    require(not facts, "Blocked: test member already has FACTs")
    for key in ("top3", "in_progress", "recent_changes"):
        require(not dashboard.get(key), "Blocked: test member already has activity")
    require(dashboard.get("confirmed_awareness_count", 0) == 0,
            "Blocked: test member already has confirmed Awareness")


def complete(client, catalog, fields):
    started = request(client, "POST", f"/v1/me/actions/{catalog}/start")
    aid = started["action_instance_id"]
    request(client, "POST", f"/v1/me/actions/{aid}/submit", json={"fields": fields})
    path = f"/v1/me/actions/{catalog}/{aid}/complete"
    first = request(client, "POST", path, json={"fields": fields})
    facts_before = request(client, "GET", "/v1/me/facts")
    dashboard_before = request(client, "GET", "/v1/me/dashboard")
    replay = request(client, "POST", path, json={"fields": fields})
    require(replay.get("idempotent") is True, "Repeated completion was not idempotent")
    require(request(client, "GET", "/v1/me/facts") == facts_before,
            "Repeated completion changed FACTs")
    require(request(client, "GET", "/v1/me/dashboard") == dashboard_before,
            "Repeated completion changed dashboard/activity")
    first["_verification_instance_id"] = aid
    return first


def run(token, household_type="couple", observer_token=None):
    require(household_type in {"single", "couple"}, "Invalid test household")
    headers = {"Authorization": f"Bearer {token}"}
    with httpx.Client(base_url=BASE_URL, headers=headers, timeout=45,
                      follow_redirects=False) as client:
        health = request(client, "GET", "/health")
        require(health.get("storage") == "supabase", "Blocked: live storage is not Supabase")
        owner_identity = request(client, "GET", "/v1/me")
        require_empty_member(request(client, "GET", "/v1/me/facts"),
                             request(client, "GET", "/v1/me/dashboard"))
        if observer_token:
            with httpx.Client(base_url=BASE_URL,
                              headers={"Authorization": f"Bearer {observer_token}"},
                              timeout=45, follow_redirects=False) as observer:
                observer_identity = request(observer, "GET", "/v1/me")
                require(observer_identity["auth_subject"] != owner_identity["auth_subject"],
                        "Blocked: isolation requires two different members")
                require_empty_member(request(observer, "GET", "/v1/me/facts"),
                                     request(observer, "GET", "/v1/me/dashboard"))
        questions = request(client, "GET", f"/v1/awareness/questions?household_type={household_type}")
        require(len(questions["questions"]) == 12, "Expected 12 Awareness questions")
        run_data = request(client, "POST", "/v1/awareness/runs",
                           json={"age_band": "50_55", "household_type": household_type})
        run_headers = {"X-Awareness-Token": run_data["run_token"]}
        run_path = f"/v1/awareness/runs/{run_data['run_id']}"
        for question in questions["questions"]:
            request(client, "PUT", f"{run_path}/answers/{question['id']}",
                    headers=run_headers, json={"response": "UNKNOWN_OR_NOT_PREPARED"})
        finalized = request(client, "POST", f"{run_path}/complete", headers=run_headers)
        claimed = request(client, "POST", "/v1/me/awareness/claim",
                          json={"handoff_token": finalized["handoff_token"]})
        before_ids = top3_ids(claimed["dashboard"])
        require(len(before_ids) == 3, "Initial Top3 missing")
        gap = "ACT_CALCULATE_INCOME_GAP"
        require(request(client, "GET", f"/v1/me/actions/{gap}")["preview"]["ready"] is False,
                "Income gap became ready before prerequisites")
        first_action = complete(client, "ACT_CONFIRM_RETIREMENT_AGE", {"retirement_age": 60})
        complete(client, "ACT_CHECK_NPS_ESTIMATE", {
            "birth_year_self": 1968, "nps_monthly_self": 1200000,
            "birth_year_spouse": 1970, "nps_monthly_spouse": 900000})
        complete(client, "ACT_ESTIMATE_RETIREMENT_BUDGET", {"retirement_budget_10k": 320})
        complete(client, "ACT_CHECK_RET_PRIVATE_PENSION", {
            "has_ret_private_pension": "YES", "ret_private_monthly_10k": 120,
            "ret_private_start_age": 60, "ret_private_years": 20})
        preview = request(client, "GET", f"/v1/me/actions/{gap}")["preview"]
        require(preview["ready"] and preview["income_gap_years"] == 4,
                "Derived income gap did not match prerequisites")
        complete(client, gap, {"bridge_sources": ["POST_RETIREMENT_WORK", "FINANCIAL_ASSETS"]})
        housing = complete(client, "ACT_DEFINE_HOUSING_PLAN", {
            "housing_tenure": "OWNER_APARTMENT", "housing_move_plan": "KEEP",
            "reverse_mortgage_plan": "UNKNOWN"})
        health_result = complete(client, "ACT_REVIEW_HEALTH_COVERAGE", {
            "critical_illness_benefit_band": "NONE_UNKNOWN",
            "indemnity_coverage": "INDEMNITY_ONLY", "major_history": "NONE",
            "income_stop_plan_checked": "NO"})
        require(housing["awareness_response"] == "PARTIAL"
                and health_result["awareness_response"] == "PARTIAL",
                "Unknown input was incorrectly marked fully confirmed")
        complete(client, "ACT_SUMMARIZE_ASSETS_DEBT", {
            "financial_asset_band": "100M_200M", "debt_band": "LT_100M"})
        complete(client, "ACT_DEFINE_POST_RETIREMENT_WORK", {"work_plan_type": "NO_WORK"})
        complete(client, "ACT_DEFINE_CARE_PLAN", {
            "care_provider": "MIXED", "care_place": "HOME", "care_cost_band": "1M_2M",
            "care_coverage_status": "RESEARCHING"})
        complete(client, "ACT_CREATE_EMERGENCY_DIGITAL_ASSET_LIST", {
            "digital_categories": ["BANK_SECURITIES", "EMAIL_SOCIAL"],
            "inventory_location_type": "DIGITAL_SECURE_FILE", "family_can_locate": "YES",
            "access_procedure_prepared": "YES"})
        complete(client, "ACT_START_FAMILY_WELLDYING_CONVERSATION", {
            "conversation_done": "YES", "preference_topics": ["CARE"]})
        facts = request(client, "GET", "/v1/me/facts")
        if household_type == "single":
            require(not any("spouse" in key for key in facts),
                    "Single household acquired spouse FACTs")
        derived = facts["cashflow.income_gap_years_to_nps_self"]
        require(derived["value"] == 4 and derived["source_type"] == "RULE_DERIVED",
                "Income-gap FACT value/source mismatch")
        for key in ("housing.reverse_mortgage_plan_q19", "health.critical_illness_benefit_band_q12"):
            require(facts[key]["status"] == "UNKNOWN" and facts[key]["value"] is None,
                    "UNKNOWN was converted to a known value")
        require(not any("monthly_shortfall" in key or "coverage_score" in key for key in facts),
                "Unexpected derived financial/coverage FACT")
        require("care.monthly_cost_exact" not in facts,
                "Care cost band was converted to an exact amount")
        require(facts["work.post_retirement.monthly_income"]["value"] == 0,
                "Explicit NO_WORK did not preserve its confirmed zero")
        require(facts["pension.ret_private.end_age"]["value"] == 80,
                "Private pension end-age rule mismatch")
        for catalog in (
            "ACT_CONFIRM_RETIREMENT_AGE", "ACT_CHECK_NPS_ESTIMATE",
            "ACT_CHECK_RET_PRIVATE_PENSION", "ACT_ESTIMATE_RETIREMENT_BUDGET",
            gap, "ACT_SUMMARIZE_ASSETS_DEBT", "ACT_DEFINE_POST_RETIREMENT_WORK",
            "ACT_DEFINE_HOUSING_PLAN", "ACT_REVIEW_HEALTH_COVERAGE", "ACT_DEFINE_CARE_PLAN",
            "ACT_CREATE_EMERGENCY_DIGITAL_ASSET_LIST", "ACT_START_FAMILY_WELLDYING_CONVERSATION",
        ):
            for endpoint in ("action-explain", "action-help"):
                payload = {"action_catalog_id": catalog}
                if endpoint == "action-help":
                    payload["question"] = "다음에 무엇을 확인하나요?"
                response = request(client, "POST", f"/v1/me/ai/{endpoint}", json=payload)
                require(response["mode"] == "deterministic_fallback",
                        "Unexpected unverified AI provider mode")
                require(set(response["fact_refs"]).issubset(facts),
                        "AI explanation referenced an absent FACT")
        dashboard = request(client, "GET", "/v1/me/dashboard")
        require(top3_ids(dashboard) != before_ids, "Top3 did not change after completion")
    with httpx.Client(base_url=BASE_URL, headers=headers, timeout=45,
                      follow_redirects=False) as fresh:
        require(request(fresh, "GET", "/v1/me/facts") == facts,
                "FACTs did not persist across a fresh HTTP connection")
        require(top3_ids(request(fresh, "GET", "/v1/me/dashboard")) == top3_ids(dashboard),
                "Top3 did not persist across a fresh HTTP connection")
        if observer_token:
            aid = first_action["_verification_instance_id"]
            with httpx.Client(base_url=BASE_URL,
                              headers={"Authorization": f"Bearer {observer_token}"},
                              timeout=45, follow_redirects=False) as observer:
                for path, payload, expected_status in (
                    (f"/v1/me/actions/{aid}/submit", {"fields": {"retirement_age": 58}}, 404),
                    (f"/v1/me/actions/{aid}/wait", None, 404),
                    (f"/v1/me/actions/ACT_CONFIRM_RETIREMENT_AGE/{aid}/complete",
                     {"fields": {"retirement_age": 58}}, 404),
                    ("/v1/me/ai/change-summary", {"action_instance_id": aid}, 404),
                    ("/v1/me/awareness/claim", {"handoff_token": finalized["handoff_token"]}, 409),
                ):
                    result = observer.post(path, json=payload)
                    require(result.status_code == expected_status,
                            "Cross-member access was not rejected as expected")
                require_empty_member(request(observer, "GET", "/v1/me/facts"),
                                     request(observer, "GET", "/v1/me/dashboard"))
            require(request(fresh, "GET", "/v1/me/facts") == facts,
                    "Cross-member attempts changed owner FACTs")
            require(request(fresh, "GET", "/v1/me/dashboard") == dashboard,
                    "Cross-member attempts changed owner dashboard")
            print("PASS: second-member reads, mutations, event and handoff isolation")
    print("PASS: 12 Action paths, API persistence, UNKNOWN, rules, Top3, replay and deterministic help")


def main():
    token = os.getenv("LIFE2_E2E_ACCESS_TOKEN", "").strip()
    if not token or os.getenv("LIFE2_E2E_DISPOSABLE_ACCOUNT") != "1":
        print("BLOCKED: secure test token and disposable-account opt-in required; no requests sent")
        return 2
    try:
        run(token, observer_token=os.getenv("LIFE2_E2E_ISOLATION_ACCESS_TOKEN") or None)
    except VerificationError as error:
        print(f"FAIL: {error}; synthetic test records may remain")
        return 1
    except Exception:
        # Exception representations may include network/request details.
        print("FAIL: verification interrupted; synthetic test records may remain")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
