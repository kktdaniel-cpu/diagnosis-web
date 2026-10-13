from uuid import uuid4
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.auth import get_current_subject
from app.store import MemoryStore
import app.main as api

@pytest.fixture
def setup(monkeypatch):
    m=MemoryStore();monkeypatch.setattr(api,'store',m)
    subject=str(uuid4());app.dependency_overrides[get_current_subject]=lambda:subject
    token=m.create_gap_preparation({})['handoff_token'];pid=m.claim_gap_preparation(token,subject)['preparation_id']
    yield m,subject,pid
    app.dependency_overrides.clear()

def test_receipt_idempotency_conflict_isolation(setup):
    m,subject,pid=setup;c=TestClient(app)
    body=dict(preparation_id=pid,request_id=str(uuid4()),topic='WORK',consent=True)
    r=c.post('/v1/me/consultations',json=body);assert r.status_code==200
    assert r.json()['data']['notification_status']=='NOT_CONFIGURED'
    assert c.post('/v1/me/consultations',json=body).json()['data']['idempotent'] is True
    assert len(m.consultations)==1 and not m.facts
    assert c.post('/v1/me/consultations',json={**body,'topic':'PENSION'}).status_code==409
    app.dependency_overrides[get_current_subject]=lambda:str(uuid4())
    assert c.post('/v1/me/consultations',json=body).status_code==404

@pytest.mark.parametrize('change',[{'consent':False},{'consent':'true'},{'topic':'UNKNOWN'},{'email':'unexpected'}])
def test_closed_consent_contract(setup,change):
    _,_,pid=setup
    b=dict(preparation_id=pid,request_id=str(uuid4()),topic='CALENDAR',consent=True);b.update(change)
    assert TestClient(app).post('/v1/me/consultations',json=b).status_code==422
