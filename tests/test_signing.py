import base64
import json
import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.exceptions import InvalidSignature
from app.signing import Signer
from test_phase1 import client, headers

def test_deterministic_public_key():
    assert Signer('test-secret-'+ 'x'*32).public == Signer('test-secret-'+ 'x'*32).public
    with pytest.raises(ValueError): Signer('short')

def test_activation_signature(client):
    issued=client.post('/admin/licenses',headers=headers(),json={}).json()
    response=client.post('/activate',json={'key':issued['key'],'machine_id':'a'*64})
    assert response.status_code==200
    result=response.json()
    public=client.get('/public-key').json()
    key=Ed25519PublicKey.from_public_bytes(base64.b64decode(public['public_key']))
    raw=base64.b64decode(result['token'])
    sig=base64.b64decode(result['signature'])
    key.verify(sig,raw)
    data=json.loads(raw)
    assert data['machine_id']=='a'*64
    assert data['license_id']==issued['license']['id']
    assert data['key_id']==public['key_id']
    assert 'private' not in public and 'key' not in data
    with pytest.raises(InvalidSignature): key.verify(sig,raw+b' ')
