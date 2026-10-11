from app.precision import precision_prefill, precision_entry_url

def fact(value, unit, status="KNOWN"):
    return {"value":value,"unit":unit,"status":status}

def test_transfer_uses_confirmed_facts_and_preserves_won_precision():
    fields={
        "profile.birth_year_self":fact(1975,"year"),
        "profile.birth_year_spouse":fact(1973,"year"),
        "pension.nps.monthly_self":fact(1505001,"KRW_per_month"),
        "pension.nps.monthly_spouse":fact(0,"KRW_per_month"),
        "work.primary_job_exit_age":fact(60,"age_years"),
        "secret.password":fact("private","text"),
    }
    assert precision_prefill(fields,"couple")==dict(household_type="couple",birth_year_self=1975,birth_year_spouse=1973,nps_monthly_self=1505001,nps_monthly_spouse=0,primary_job_exit_age=60)
    single=precision_prefill(fields,"single")
    assert "birth_year_spouse" not in single and "nps_monthly_spouse" not in single
    assert "secret.password" not in single

def test_unconfirmed_wrong_unit_and_invalid_values_are_not_transferred():
    fields={"profile.birth_year_self":fact(1975,"year","UNKNOWN"),"pension.nps.monthly_self":fact(150,"10k_KRW_per_month"),"work.primary_job_exit_age":fact(True,"age_years")}
    assert precision_prefill(fields,"couple")=={"household_type":"couple"}
    assert precision_entry_url("https://diag.lpp20.com/")=="https://diag.lpp20.com/life2-precision.html"
    assert precision_entry_url("https://other.test/")=="https://other.test/"

def test_endpoint_reads_only_authenticated_subject_and_does_not_mutate(monkeypatch):
    from fastapi.testclient import TestClient
    from app.auth import get_current_subject
    from app import main
    calls=[]
    monkeypatch.setattr(main.store,"member_awareness",lambda subject: calls.append(("awareness",subject)) or {"household_type":"single"})
    monkeypatch.setattr(main.store,"member_facts",lambda subject: calls.append(("facts",subject)) or {"pension.nps.monthly_self":fact(1500000,"KRW_per_month")})
    monkeypatch.setattr(main,"PRECISION_URL","https://diag.lpp20.com/")
    main.app.dependency_overrides[get_current_subject]=lambda:"synthetic-test-user"
    try:
        result=TestClient(main.app).get("/v1/me/precision/entry")
        assert result.status_code==200
        assert result.json()["data"]["prefill"]=={"household_type":"single","nps_monthly_self":1500000}
        assert calls==[("awareness","synthetic-test-user"),("facts","synthetic-test-user")]
    finally:
        main.app.dependency_overrides.clear()
