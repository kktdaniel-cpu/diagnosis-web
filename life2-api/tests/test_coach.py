from app.coach import build_action_context, explain_action, help_action

def test_context_includes_only_action_relevant_facts_and_preserves_unknown():
    facts={
        "pension.nps.monthly_self":{
            "fact_key":"pension.nps.monthly_self",
            "status":"KNOWN",
            "value":1200000,
            "unit":"KRW_per_month",
            "source_type":"USER_CONFIRMED",
            "source_ref":"ACT_CHECK_NPS_ESTIMATE",
            "verification_level":"SELF_REPORTED",
        },
        "pension.nps.monthly_spouse":{
            "fact_key":"pension.nps.monthly_spouse",
            "status":"UNKNOWN",
            "value":"SHOULD_NOT_LEAK_AS_VALUE",
            "unit":"KRW_per_month",
            "source_type":"USER_CONFIRMED",
            "source_ref":"ACT_CHECK_NPS_ESTIMATE",
            "verification_level":"SELF_REPORTED",
        },
        "care.monthly_cost_band":{
            "fact_key":"care.monthly_cost_band",
            "status":"KNOWN",
            "value":"1M_2M",
            "unit":"care_cost_band",
            "source_type":"USER_CONFIRMED",
            "source_ref":"ACT_DEFINE_CARE_PLAN",
            "verification_level":"SELF_REPORTED",
        },
    }
    awareness={"answers":{"AWR_Q02_NPS":"PARTIAL"}}
    dashboard={"top3":[{"action_catalog_id":"ACT_CHECK_NPS_ESTIMATE","priority_class":"P1","reason_code":"AWR_Q02_NPS:PARTIAL"}]}
    ctx=build_action_context("ACT_CHECK_NPS_ESTIMATE",facts,awareness,dashboard)
    keys=[x["fact_key"] for x in ctx["relevant_facts"]]
    assert "pension.nps.monthly_self" in keys
    assert "pension.nps.monthly_spouse" in keys
    assert "care.monthly_cost_band" not in keys
    spouse=next(x for x in ctx["relevant_facts"] if x["fact_key"]=="pension.nps.monthly_spouse")
    assert spouse["status"]=="UNKNOWN"
    assert spouse["value"] is None

def test_context_excludes_secret_shaped_fact_keys():
    facts={
        "digital_legacy.inventory_categories":{
            "fact_key":"digital_legacy.inventory_categories",
            "status":"KNOWN",
            "value":["CRYPTO"],
            "unit":"category_list",
            "source_type":"USER_CONFIRMED",
        },
        "digital_legacy.password":{
            "fact_key":"digital_legacy.password",
            "status":"KNOWN",
            "value":"never",
            "source_type":"USER_CONFIRMED",
        },
    }
    ctx=build_action_context(
        "ACT_CREATE_EMERGENCY_DIGITAL_ASSET_LIST",
        facts,
        {"answers":{"AWR_Q11_DIGITAL_FAMILY_INFO":"UNKNOWN_OR_NOT_PREPARED"}},
        {"top3":[]},
    )
    keys=[x["fact_key"] for x in ctx["relevant_facts"]]
    assert "digital_legacy.inventory_categories" in keys
    assert "digital_legacy.password" not in keys

def test_explain_does_not_rerank_action():
    ctx=build_action_context(
        "ACT_CONFIRM_RETIREMENT_AGE",
        {},
        {"answers":{"AWR_Q01_RETIREMENT_AGE":"UNKNOWN_OR_NOT_PREPARED"}},
        {"top3":[{"action_catalog_id":"ACT_CONFIRM_RETIREMENT_AGE","priority_class":"P1"}]},
    )
    out=explain_action("ACT_CONFIRM_RETIREMENT_AGE",ctx)
    assert out["action_catalog_id"]=="ACT_CONFIRM_RETIREMENT_AGE"
    assert out["source_type"]=="RULE_DERIVED"
    assert "score" not in str(out).lower()

def test_digital_help_warns_against_secrets():
    ctx=build_action_context(
        "ACT_CREATE_EMERGENCY_DIGITAL_ASSET_LIST",
        {},
        {"answers":{"AWR_Q11_DIGITAL_FAMILY_INFO":"UNKNOWN_OR_NOT_PREPARED"}},
        {"top3":[]},
    )
    out=help_action("ACT_CREATE_EMERGENCY_DIGITAL_ASSET_LIST","비밀번호도 적나요?",ctx)
    assert out["secret_warning"]
    assert "PIN" in out["secret_warning"]
    assert out["mode"]=="deterministic_fallback"


def test_change_summary_is_traceable_to_event_metadata():
    from app.coach import summarize_change
    event={
        "event_id":"evt-1",
        "action_instance_id":"act-1",
        "action_catalog_id":"ACT_CONFIRM_RETIREMENT_AGE",
        "metadata":{
            "fact_keys":["work.primary_job_exit_age"],
            "top3_before":["A","B","C"],
            "top3_after":["B","C","D"],
            "top3_changed":True,
        },
    }
    out=summarize_change(event)
    assert out["fact_refs"]==["work.primary_job_exit_age"]
    assert out["top3_changed"] is True
    assert out["top3_before"]==["A","B","C"]
    assert out["top3_after"]==["B","C","D"]
    assert "점수" not in out["message"]


def test_change_summary_endpoint_reads_completed_action_event():
    from app.auth import get_current_subject
    from app.catalog import QUESTIONS
    from app.main import app
    from fastapi.testclient import TestClient

    client=TestClient(app)
    created=client.post("/v1/awareness/runs",json={"age_band":"50_55","household_type":"couple"}).json()["data"]
    headers={"X-Awareness-Token":created["run_token"]}
    for q in QUESTIONS:
        assert client.put(
            f"/v1/awareness/runs/{created['run_id']}/answers/{q['id']}",
            json={"response":"UNKNOWN_OR_NOT_PREPARED"},
            headers=headers,
        ).status_code==200
    done=client.post(f"/v1/awareness/runs/{created['run_id']}/complete",headers=headers).json()["data"]
    app.dependency_overrides[get_current_subject]=lambda:"summary-user"
    try:
        assert client.post("/v1/me/awareness/claim",json={"handoff_token":done["handoff_token"]}).status_code==200
        start=client.post("/v1/me/actions/ACT_CONFIRM_RETIREMENT_AGE/start").json()["data"]
        complete=client.post(
            f"/v1/me/actions/ACT_CONFIRM_RETIREMENT_AGE/{start['action_instance_id']}/complete",
            json={"fields":{"retirement_age":60}},
        )
        assert complete.status_code==200
        assert complete.json()["data"]["event_id"]
        summary=client.post(
            "/v1/me/ai/change-summary",
            json={"action_instance_id":start["action_instance_id"]},
        )
        assert summary.status_code==200
        data=summary.json()["data"]
        assert data["action_catalog_id"]=="ACT_CONFIRM_RETIREMENT_AGE"
        assert "work.primary_job_exit_age" in data["fact_refs"]
    finally:
        app.dependency_overrides.clear()
