# Farmers — licencias, fase 1

Backend independiente del launcher. Solo crea y consulta licencias. No implementa activación, fingerprint, firmas, revocación ni cambios en el .exe.

## 1. GitHub

Crea un repositorio privado vacío llamado, por ejemplo, `farmers-licenses`. Sube **el contenido de esta carpeta a la raíz**: `app`, `alembic`, `tests`, `.github`, los requisitos y demás archivos. Incluye los archivos ocultos `.gitignore` y `.github/workflows/tests.yml`. No subas secretos ni las carpetas del launcher.

En Actions debe aparecer `Phase 1 tests`. Ejecuta pruebas con una base PostgreSQL 18 desechable alojada en GitHub. No usa tu base de Neon. Si Actions está deshabilitado, actívalo para el repositorio. Espera al resultado verde antes de desplegar. Las cuotas de Actions de tu cuenta aplican.

## 2. Render

Opción recomendada: New → Blueprint y selecciona el repositorio. `render.yaml` propone Frankfurt y plan Free, genera ADMIN_TOKEN y pide DATABASE_URL. Revisa que Render siga mostrando el plan gratuito antes de crear el servicio.

En Neon → Connect, selecciona la base y copia la **URL de conexión directa, sin pooling**, con `sslmode=require`. Pega solo la URL `postgresql://...`, sin `psql` ni comillas, en DATABASE_URL. Se usa conexión directa también para las migraciones. No publiques la URL ni capturas con sus credenciales.

Si prefieres crear un Web Service manualmente:

- Runtime: Python; región: Frankfurt; plan: Free.
- Build Command: `pip install -r requirements.txt`
- Start Command: `alembic upgrade head && uvicorn app.main:create_app --factory --host 0.0.0.0 --port $PORT --workers 1 --no-access-log`
- Health Check Path: `/health`
- Environment: `PYTHON_VERSION=3.13.7`, `DATABASE_URL` y `ADMIN_TOKEN`.
- ADMIN_TOKEN debe ser un secreto aleatorio de al menos 32 caracteres. Usa un generador de contraseñas; no una contraseña habitual.

El código conserva los parámetros SSL de Neon y selecciona el driver psycopg. Cada arranque aplica migraciones pendientes. Mantener una instancia/un worker en esta fase; antes de escalar habrá que separar la ejecución de migraciones. No se guarda SQLite ni información persistente en el disco de Render.

## 3. Validación online

1. Abre `https://TU-SERVICIO.onrender.com/health`: debe devolver `{"status":"ok","phase":1}`.
2. Abre `/licenses` sin credenciales: debe responder HTTP 401. Esto es correcto.
3. Desde tu equipo, en esta carpeta, ejecuta:

   `py generate_license.py --url https://TU-SERVICIO.onrender.com --notes "Prueba fase 1"`

4. Introduce ADMIN_TOKEN cuando se solicite (no se muestra mientras escribes). Aparecerá una KEY y sus metadatos. Guarda la KEY: no se podrá consultar otra vez.
5. Ejecuta:

   `py generate_license.py --url https://TU-SERVICIO.onrender.com --list`

   Debe aparecer la licencia con estado `unused`, sin KEY completa ni hash.
6. En Neon, SQL Editor, consulta:

   `SELECT id, product_id, key_prefix, status, activation_count FROM licenses;`

7. Reinicia el servicio y repite el listado: la licencia debe permanecer.

Esta utilidad requiere Python solo en el equipo administrador. No ejecuta un backend local, no necesita instalar dependencias y no se distribuye con el launcher.

## Alcance y seguridad

- GET `/health` comprueba conectividad con la base; no revela credenciales.
- GET `/licenses` tiene paginación `limit`/`offset` y autenticación Bearer.
- POST `/admin/licenses` permite `product_id`, `notes` y `max_activations`. Devuelve la clave completa únicamente al crearla. Es el mínimo administrativo necesario para generar desde fuera de Render Free; no es todavía el panel de administración.
- Las claves se generan con `secrets`, se almacena SHA-256 y un prefijo, y la base impone unicidad. El formato de 16 caracteres tiene aproximadamente 79 bits de entropía con el alfabeto elegido.
- ADMIN_TOKEN solo lo conserva el administrador y Render. Nunca se añade al cliente ni a GitHub. HTTPS se termina en Render. No se habilitan CORS ni documentación pública. No hay logging propio de cuerpos o claves y las respuestas incluyen `Cache-Control: no-store`.
- No hay recuperador de claves completas. Si se pierde la respuesta de creación, consulta el listado antes de repetir para evitar generar una licencia adicional por accidente.
- El token administrativo inicial es una credencial estática: todavía no hay usuarios, sesiones, rate limiting ni historial administrativo. No compartirlo con usuarios finales. Las licencias de prueba aún no protegen ningún programa.
- Render Free puede tardar en despertar; la CLI espera hasta 120 segundos y no reintenta POST automáticamente.
- Dependencias acotadas por versión mayor, aún sin lock exacto. Revisar el resultado de CI antes de aceptar el despliegue.

## Estado de verificación de esta entrega

Se comprobó la sintaxis de los archivos Python. Se incluyeron tests de autorización, generación, almacenamiento sin clave, colisión forzada y schemas, más `alembic check`. **No se han ejecutado todavía los tests con PostgreSQL ni se ha desplegado este backend en Render/Neon.** Esa validación se realizará en GitHub y en tu servicio antes de pasar a fase 2.

Fuentes: https://render.com/docs/deploy-fastapi y https://docs.sqlalchemy.org/en/20/dialects/postgresql.html#module-sqlalchemy.dialects.postgresql.psycopg
