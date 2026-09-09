import re
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, delete
from sqlalchemy.orm import Session
from app.config import Settings
from app.database import build_engine
from app.main import create_app
from app.models import License
from app import licenses

@pytest.fixture
def client():
    settings = Settings()
    if not (settings.sqlalchemy_url().database or '').endswith('_test'):
        pytest.fail('Los tests solo pueden ejecutarse contra una base cuyo nombre termine en _test.')
    engine = build_engine(settings)
    with Session(engine) as session:
        session.execute(delete(License))
        session.commit()
    with TestClient(create_app(settings)) as value:
        yield value
    engine.dispose()

def headers():
    return {'Authorization': 'Bearer ' + Settings().admin_token.get_secret_value()}

def test_access(client):
    assert client.get('/health').json()['status'] == 'ok'
    assert client.get('/licenses').status_code == 401
    assert client.post('/admin/licenses', json={}).status_code == 401
    assert client.get('/licenses', headers={'Authorization':'Bearer invalid'}).status_code == 401
    assert client.get('/docs').status_code == 404

def test_issue_and_storage(client):
    response = client.post('/admin/licenses', json={}, headers=headers())
    assert response.status_code == 201
    data = response.json()
    assert re.fullmatch(r'[A-Z2-9]{4}(-[A-Z2-9]{4}){3}', data['key'])
    listing = client.get('/licenses', headers=headers())
    assert listing.headers['cache-control'] == 'no-store'
    assert data['key'] not in listing.text and 'key_hash' not in listing.text
    assert listing.json()[0]['status'] == 'unused'
    engine = build_engine(Settings())
    with Session(engine) as session:
        row = session.scalar(select(License))
        assert row.key_hash == licenses.key_hash(data['key'])
        assert row.activation_count == 0 and row.machine_id is None
        assert data['key'] not in str(row.__dict__)
    engine.dispose()

def test_duplicate_retry(client, monkeypatch):
    keys = iter(['AAAA-AAAA-AAAA-AAAA','AAAA-AAAA-AAAA-AAAA','BBBB-BBBB-BBBB-BBBB'])
    monkeypatch.setattr(licenses, 'generate_key', lambda: next(keys))
    for expected in ('AAAA-AAAA-AAAA-AAAA','BBBB-BBBB-BBBB-BBBB'):
        assert client.post('/admin/licenses', json={}, headers=headers()).json()['key'] == expected
    assert len(client.get('/licenses', headers=headers()).json()) == 2

@pytest.mark.parametrize('body', [{'max_activations':0}, {'status':'active'}, {'product_id':'../x'}, {'max_activations':True}])
def test_validation(client, body):
    assert client.post('/admin/licenses', json=body, headers=headers()).status_code == 422
