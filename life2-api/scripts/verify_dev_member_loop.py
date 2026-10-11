"""Opt-in live dev API checks; leaves synthetic data on a disposable account.

Supply LIFE2_E2E_ACCESS_TOKEN through a secure environment, never a command argument.
Set LIFE2_E2E_DISPOSABLE_ACCOUNT=1 only for a fresh, dedicated test member.
This does not test browser login, signup UI, PDF, or cross-member isolation.
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
    return first


def run(token):
    headers = {"Authorization": f"Bearer {token}"}
    with httpx.Client(base_url=BASE_URL, headers=headers, timeout=45,
                      follow_redirects=False) as client:
        health = request(client, "GET", "/health")
        require(health.get("storage") == "supabase", "Blocked: live storage is not Supabase")
        request(client, "GET", "/v1/me")
        require_empty_member(request(client, "GET", "/v1/me/facts"),
                             request(client, "GET", "/v1/me/dashboard"))
        questions = request(client, "GET", "/v1/awareness/questions?household_type=couple")
        require(len(questions["questions"]) == 12, "Expected 12 Awareness questions")
        run_data = request(client, "POST", "/v1/awareness/runs",
                           json={"age_band": "50_55", "household_type": "couple"})
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
        complete(client, "ACT_CONFIRM_RETIREMENT_AGE", {"retirement_age": 60})
        complete(client, "ACT_CHECK_NPS_ESTIMATE", {
            "birth_year_self": 1968, "nps_monthly_self": 1200000,
            "birth_year_spouse": 1970, "nps_monthly_spouse": 900000})
        complete(client, "ACT_ESTIMATE_RETIREMENT_BUDGET", {"retirement_budget_10k": 320})
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
        facts = request(client, "GET", "/v1/me/facts")
        derived = facts["cashflow.income_gap_years_to_nps_self"]
        require(derived["value"] == 4 and derived["source_type"] == "RULE_DERIVED",
                "Income-gap FACT value/source mismatch")
        for key in ("housing.reverse_mortgage_plan_q19", "health.critical_illness_benefit_band_q12"):
            require(facts[key]["status"] == "UNKNOWN" and facts[key]["value"] is None,
                    "UNKNOWN was converted to a known value")
        require(not any("monthly_shortfall" in key or "coverage_score" in key for key in facts),
                "Unexpected derived financial/coverage FACT")
        dashboard = request(client, "GET", "/v1/me/dashboard")
        require(top3_ids(dashboard) != before_ids, "Top3 did not change after completion")
    with httpx.Client(base_url=BASE_URL, headers=headers, timeout=45,
                      follow_redirects=False) as fresh:
        require(request(fresh, "GET", "/v1/me/facts") == facts,
                "FACTs did not persist across a fresh HTTP connection")
        require(top3_ids(request(fresh, "GET", "/v1/me/dashboard")) == top3_ids(dashboard),
                "Top3 did not persist across a fresh HTTP connection")
    print("PASS: dev API persistence, UNKNOWN, prerequisites, Top3 and completion replay")


def main():
    token = os.getenv("LIFE2_E2E_ACCESS_TOKEN", "").strip()
    if not token or os.getenv("LIFE2_E2E_DISPOSABLE_ACCOUNT") != "1":
        print("BLOCKED: secure test token and disposable-account opt-in required; no requests sent")
        return 2
    try:
        run(token)
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
