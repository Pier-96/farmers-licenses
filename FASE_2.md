# Fase 2 — activación por equipo

## Actualizar

Sube el contenido del ZIP a la raíz del mismo repositorio, reemplazando los archivos existentes. No cambies DATABASE_URL ni ADMIN_TOKEN. No hay migración nueva ni se borran licencias existentes. Espera a que GitHub Actions esté verde y Render despliegue el commit nuevo. Si Render despliega automáticamente antes de CI, no pruebes activaciones hasta que CI termine correctamente.

GET `/health` ahora devuelve `{"status":"ok","phase":2}`. El launcher no cambia y aún no consume estas licencias.

## Endpoint

POST `/activate` con JSON:

```json
{"key":"XXXX-XXXX-XXXX-XXXX","machine_id":"64 caracteres hexadecimales"}
```

No requiere ADMIN_TOKEN: la KEY es la credencial del usuario. Los endpoints administrativos continúan protegidos. Aún no se obtiene un fingerprint real ni se emiten tokens firmados: eso corresponde a las fases siguientes.

| Situación | HTTP | code |
|---|---|---|
| Primera activación | 200 | LICENSE_ACTIVATED |
| Ya activa en el mismo ID | 200 | LICENSE_ALREADY_ACTIVE_ON_THIS_DEVICE |
| Otro ID | 409 | LICENSE_ALREADY_BOUND |
| KEY inexistente | 400 | LICENSE_INVALID |
| Revocada | 403 | LICENSE_REVOKED |
| Límite histórico agotado | 403 | LICENSE_ACTIVATION_LIMIT_REACHED |
| Formato incorrecto | 422 | Respuesta genérica sin valores enviados |

La respuesta correcta incluye license_id y product_id, nunca la KEY ni datos de otro dispositivo. La primera activación cambia estado, machine_id, fecha y contador. La repetición en el mismo dispositivo no consume otra activación, incluso si se alcanzó el límite histórico. Una revocación prevalece sobre la idempotencia. last_validation_at se reserva para la futura validación online.

## Prueba real en Render/Neon

1. Genera una licencia NUEVA de prueba:

   `py generate_license.py --url https://farmers-licenses.onrender.com --notes "Prueba fase 2"`

2. Guarda la KEY y ejecuta:

   `py test_activation_remote.py --url https://farmers-licenses.onrender.com`

3. Introduce esa KEY cuando se solicite. No se muestra mientras escribes. El script usa los IDs ficticios A y B, no datos de tu ordenador. La licencia quedará vinculada a A; el reset administrativo todavía no está implementado.
4. Debe mostrar LICENSE_ACTIVATED, LICENSE_ALREADY_ACTIVE_ON_THIS_DEVICE y LICENSE_ALREADY_BOUND, y terminar en PASS.
5. Ejecuta el listado administrativo. Esa licencia debe estar active, machine_id con 64 letras a y activation_count=1. Las demás no cambian.

## Pruebas y límites

Los tests de GitHub utilizan una base desechable terminada en _test. Cubren estados, formato inválido, repetición, límites y dos solicitudes concurrentes desde el mismo equipo y desde equipos distintos. La transacción PostgreSQL usa SELECT FOR UPDATE con espera acotada para bloquear la fila hasta confirmar su asignación.

La firma, identificación real del equipo, reset, validación periódica y rate limiting siguen pendientes. El machine_id enviado en esta fase es una declaración del cliente, no una prueba de hardware. Esta fase no protege todavía el .exe. No pasar a fase 3 hasta que CI y la comprobación online sean satisfactorias.

Validación de esta entrega: sintaxis Python comprobada; tests PostgreSQL preparados pero pendientes de ejecución en GitHub y prueba online pendiente. No se han usado tus secretos ni se ha accedido a Neon desde el entorno de desarrollo.
