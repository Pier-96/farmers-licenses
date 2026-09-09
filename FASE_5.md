# Fase 5 — firma Ed25519

## Backend: actualizar primero

Sube el contenido del ZIP backend fase 5 al mismo repositorio, incluidos render.yaml y .github. No hay migraciones nuevas ni se borran licencias. GitHub usa un secreto de firma exclusivamente de prueba: NO lo copies a Render.

El Blueprint añade PRIVATE_SIGNING_KEY con generateValue:true. Sincroniza/aplica el Blueprint en Render para que genere el nuevo secreto antes del despliegue. Si el despliegue automático arranca antes de añadirlo fallará de forma cerrada; configura el secreto y vuelve a desplegar. No cambies DATABASE_URL ni ADMIN_TOKEN.

PRIVATE_SIGNING_KEY es un secreto aleatorio de al menos 32 caracteres, no una KEY de licencia ni una contraseña elegida a mano. El backend deriva de él la semilla Ed25519 con SHA-256 y separación de dominio; tanto el secreto como la clave privada derivada deben permanecer exclusivamente en Render. No se generan ni guardan en disco. No regeneres este secreto en reinicios ni en cada deploy: cambiarlo cambia la clave pública y obliga a actualizar los clientes.

Si creaste el servicio manualmente, añade un valor generado de forma criptográficamente aleatoria mediante la gestión de secretos; la opción Blueprint evita tener que generar la privada en el equipo de desarrollo. Mantén una copia de recuperación en tu gestor de secretos administrativo si tu política lo requiere, nunca en repositorios o ZIPs.

Espera CI verde. /health debe indicar phase:5. Después abre:

https://farmers-licenses.onrender.com/public-key

Devuelve algorithm, key_id y public_key. Estos campos son públicos; PRIVATE_SIGNING_KEY nunca se devuelve. Solo la respuesta /activate incluye token y signature además de los campos anteriores. Tanto la primera activación como la reactivación idempotente reciben un token firmado.

## Cliente: configurar después

Extrae el ZIP cliente en otra carpeta. Ejecuta PREPARAR.bat. Ejecuta `py configurar_clave_publica.py` y pega únicamente public_key y key_id obtenidos de tu propio servicio HTTPS.

Esto fija explícitamente la confianza en licensing/public_keys.py. El launcher nunca descarga automáticamente una nueva clave pública para aceptar una firma. No se incrusta ningún secreto administrativo. Después de configurar, puedes construir el EXE con CREAR_EXE.bat y distribuirlo sin la herramienta de configuración.

Prueba INICIAR.bat con tu KEY ya vinculada al PC real. Debe abrirse y conservar activation_count=1. Repite tras reiniciar el servicio: debe seguir aceptando la firma, porque la clave pública no debe cambiar.

## Validación y límites

13 pruebas del cliente pasan y se verificó interoperabilidad real entre firmador y verificador usando claves efímeras de test. Los tests de backend con PostgreSQL y el despliegue real quedan pendientes de GitHub/Render.

Se verifica firma, clave pública fijada, versión, producto, machine_id, identificador y fechas. Los tokens manipulados, de otro equipo o firmados por una clave no confiable se rechazan. expires_at=null en esta fase; no se guarda el token ni se permite acceso offline. Se sigue pidiendo KEY al iniciar y el backend comprueba su estado cada vez.

Los tokens no contienen la KEY original. El almacenamiento DPAPI llega en fase 6. La vigencia offline, generación de activación y rechazo de tokens antiguos tras reset deberán añadirse antes de habilitar reutilización offline y reset. Esta fase no impide modificar un cliente Python; las versiones anteriores tampoco pasan a verificar firmas automáticamente.

No pasar a fase 6 hasta comprobar CI, /health, firma pública estable y activación real desde el cliente actualizado.
