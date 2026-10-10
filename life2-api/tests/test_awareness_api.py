from fastapi.testclient import TestClient
from app.main import app
from app.catalog import QUESTIONS

client=TestClient(app)

def test_health():
    r=client.get('/health')
    assert r.status_code==200
    assert r.json()['ok'] is True

def test_full_awareness_flow():
    r=client.post('/v1/awareness/runs',json={'age_band':'50_55','household_type':'couple'})
    assert r.status_code==200
    run_id=r.json()['data']['run_id']
    token=r.json()['data']['run_token']
    headers={'X-Awareness-Token':token}
    for q in QUESTIONS:
        x=client.put(
            f'/v1/awareness/runs/{run_id}/answers/{q["id"]}',
            json={'response':'UNKNOWN_OR_NOT_PREPARED'},
            headers=headers
        )
        assert x.status_code==200
    done=client.post(f'/v1/awareness/runs/{run_id}/complete',headers=headers)
    assert done.status_code==200
    data=done.json()['data']
    assert len(data['top3'])==3
    assert data['handoff_token']

def test_awareness_token_required():
    r=client.post('/v1/awareness/runs',json={'age_band':'50_55','household_type':'single'})
    run_id=r.json()['data']['run_id']
    qid=QUESTIONS[0]['id']
    denied=client.put(
        f'/v1/awareness/runs/{run_id}/answers/{qid}',
        json={'response':'CONFIRMED'}
    )
    assert denied.status_code==403
