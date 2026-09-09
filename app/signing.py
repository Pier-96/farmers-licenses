"""Ed25519. El secreto de generación vive únicamente en el entorno del backend."""
import base64
import hashlib
import json
from datetime import datetime, timezone
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

class Signer:
    def __init__(self, secret):
        # Render generateValue entrega un secreto aleatorio. No es una contraseña humana.
        if len(secret) < 32 or secret.startswith('REPLACE_'):
            raise ValueError('PRIVATE_SIGNING_KEY debe ser un secreto aleatorio de al menos 32 caracteres.')
        seed = hashlib.sha256(b'multicliente-ed25519-v1\0' + secret.encode('utf-8')).digest()
        self.private = Ed25519PrivateKey.from_private_bytes(seed)
        raw = self.private.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
        self.public = base64.b64encode(raw).decode('ascii')
        self.key_id = hashlib.sha256(raw).hexdigest()[:16]

    def sign(self, license_id, product_id, machine_id):
        payload = {'version':1, 'key_id':self.key_id, 'license_id':license_id,
                   'product_id':product_id, 'machine_id':machine_id,
                   'issued_at':datetime.now(timezone.utc).isoformat(), 'expires_at':None}
        raw = json.dumps(payload, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode('ascii')
        return {'token':base64.b64encode(raw).decode('ascii'),
                'signature':base64.b64encode(self.private.sign(raw)).decode('ascii')}
