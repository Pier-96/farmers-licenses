from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient
from test_phase1 import client, headers
from app.config import Settings
from app.database import build_engine
from app.models import License
from app.main import create_app

A, B = 'a'*64, 'b'*64

def new(client):
    response = client.post('/admin/licenses', headers=headers(), json={})
    assert response.status_code == 201
    return response.json()

def request(client, key, machine=A):
    return client.post('/activate', json={'key': key, 'machine_id': machine})

def row_values(license_id, **updates):
    engine = build_engine(Settings())
    try:
        with Session(engine) as session:
            row = session.get(License, license_id)
            for name, value in updates.items():
                setattr(row, name, value)
            session.commit()
            return row.machine_id, row.activation_count, row.activated_at
    finally:
        engine.dispose()

def test_activation_idempotence_and_other_pc(client):
    data = new(client)
    response = request(client, data['key'])
    assert response.status_code == 200
    assert response.json()['code'] == 'LICENSE_ACTIVATED'
    initial = row_values(data['license']['id'])
    assert initial[0:2] == (A, 1) and initial[2] is not None
    response = request(client, data['key'].lower(), A.upper())
    assert response.json()['code'] == 'LICENSE_ALREADY_ACTIVE_ON_THIS_DEVICE'
    assert row_values(data['license']['id']) == initial
    response = request(client, data['key'], B)
    assert response.status_code == 409
    assert response.json() == {'code': 'LICENSE_ALREADY_BOUND'}
    assert row_values(data['license']['id']) == initial

def test_invalid_and_revoked(client):
    assert request(client, 'ZZZZ-ZZZZ-ZZZZ-ZZZZ').json()['code'] == 'LICENSE_INVALID'
    data = new(client)
    row_values(data['license']['id'], status='revoked')
    assert request(client, data['key']).json()['code'] == 'LICENSE_REVOKED'

def test_limit_and_transaction_rollback(client):
    data = new(client)
    row_values(data['license']['id'], activation_count=1)
    response = request(client, data['key'])
    assert response.status_code == 403
    assert response.json()['code'] == 'LICENSE_ACTIVATION_LIMIT_REACHED'
    assert row_values(data['license']['id'])[0] is None

@pytest.mark.parametrize('machine', ['', 'x'*64, 'a'*63, 12, None])
def test_bad_machine(client, machine):
    response = request(client, 'AAAA-AAAA-AAAA-AAAA', machine)
    assert response.status_code == 422
    assert 'AAAA' not in response.text

def test_malformed_request(client):
    assert request(client, 'not-a-key').status_code == 422
    assert client.post('/activate', json={'key':'AAAA-AAAA-AAAA-AAAA', 'machine_id':A, 'status':'active'}).status_code == 422

@pytest.mark.parametrize('devices', [(A, B), (A, A)])
def test_concurrent_activation(client, devices):
    data = new(client)
    barrier = Barrier(2)
    def worker(device):
        with TestClient(create_app(Settings())) as other:
            barrier.wait(timeout=10)
            return request(other, data['key'], device).json()['code']
    with ThreadPoolExecutor(max_workers=2) as pool:
        codes = list(pool.map(worker, devices))
    assert codes.count('LICENSE_ACTIVATED') == 1
    expected = 'LICENSE_ALREADY_BOUND' if devices[0] != devices[1] else 'LICENSE_ALREADY_ACTIVE_ON_THIS_DEVICE'
    assert codes.count(expected) == 1
    assert row_values(data['license']['id'])[1] == 1
