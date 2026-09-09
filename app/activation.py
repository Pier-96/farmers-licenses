from datetime import datetime, timezone
from sqlalchemy import select, text
from .models import License
from .licenses import key_hash

class ActivationDenied(Exception):
    def __init__(self, code, status):
        self.code, self.status = code, status

def activate(session, request):
    # La lectura y la actualización se hacen bajo el mismo bloqueo de fila.
    # Un segundo intento espera y comprueba el estado ya confirmado del primero.
    with session.begin():
        session.execute(text("SET LOCAL lock_timeout = '5s'"))
        row = session.scalar(select(License).where(
            License.key_hash == key_hash(request.key)).with_for_update())
        if row is None:
            raise ActivationDenied('LICENSE_INVALID', 400)
        if row.status == 'revoked' or row.revoked_at is not None:
            raise ActivationDenied('LICENSE_REVOKED', 403)
        if row.status == 'active':
            if row.machine_id != request.machine_id:
                raise ActivationDenied('LICENSE_ALREADY_BOUND', 409)
            return {'code': 'LICENSE_ALREADY_ACTIVE_ON_THIS_DEVICE',
                    'license_id': row.id, 'product_id': row.product_id}
        if row.status != 'unused' or row.machine_id is not None:
            raise ActivationDenied('LICENSE_INVALID', 400)
        if row.activation_count >= row.max_activations:
            raise ActivationDenied('LICENSE_ACTIVATION_LIMIT_REACHED', 403)
        row.machine_id = request.machine_id
        row.status = 'active'
        row.activated_at = datetime.now(timezone.utc)
        row.activation_count += 1
        result = {'code': 'LICENSE_ACTIVATED', 'license_id': row.id,
                  'product_id': row.product_id}
    return result
