"""Cliente administrativo remoto. Solo necesita Python; no conecta directamente a Neon."""
import argparse
import getpass
import json
import urllib.request
import urllib.error
from urllib.parse import urlsplit

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', required=True, help='https://TU-SERVICIO.onrender.com')
    parser.add_argument('--list', action='store_true')
    parser.add_argument('--notes', default=None)
    args = parser.parse_args()
    parsed = urlsplit(args.url)
    if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.query or parsed.fragment:
        parser.error('Usa la URL HTTPS del servidor, sin credenciales ni parámetros.')
    token = getpass.getpass('ADMIN_TOKEN (entrada oculta): ')
    body = None if args.list else json.dumps({'notes': args.notes}).encode()
    request = urllib.request.Request(args.url.rstrip('/') + ('/licenses' if args.list else '/admin/licenses'),
        data=body, headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'})
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *args, **kwargs):
            return None
    try:
        with urllib.request.build_opener(NoRedirect).open(request, timeout=120) as response:
            result = json.load(response)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        if not args.list:
            print('Guarda la KEY: el servidor no permite recuperarla después.')
    except urllib.error.HTTPError as exc:
        print(f'El servidor devolvió HTTP {exc.code}.')
        return 1
    except Exception:
        print('No se pudo completar la solicitud. No se reintenta automáticamente: puede haberse creado la licencia. Consulta --list antes de repetir.')
        return 1
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
