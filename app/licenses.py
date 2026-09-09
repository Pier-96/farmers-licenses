import hashlib
import secrets
import uuid
from datetime import datetime, timezone
from sqlalchemy.exc import IntegrityError
from .models import License

ALPHABET = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'

def generate_key():
    return '-'.join(''.join(secrets.choice(ALPHABET) for _ in range(4)) for _ in range(4))

def key_hash(key):
    normalized = key.strip().upper().replace('-', '')
    return hashlib.sha256(normalized.encode('ascii')).hexdigest()

def issue(session, request):
    for _ in range(5):
        key = generate_key()
        row = License(id=str(uuid.uuid4()), key_hash=key_hash(key), key_prefix=key[:4],
                      created_at=datetime.now(timezone.utc), status='unused',
                      activation_count=0, **request.model_dump())
        session.add(row)
        try:
            session.commit()
            session.refresh(row)
            return key, row
        except IntegrityError as exc:
            session.rollback()
            # Reintentar solo colisiones de unicidad PostgreSQL.
            if getattr(exc.orig, 'sqlstate', None) != '23505':
                raise
    raise RuntimeError('No se pudo generar una clave única.')
