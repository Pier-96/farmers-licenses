"""Prueba online con una KEY desechable; no obtiene IDs reales del equipo."""
import argparse
import getpass
import json
import urllib.request
import urllib.error
from urllib.parse import urlsplit

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', required=True)
    args = parser.parse_args()
    url = urlsplit(args.url)
    if url.scheme != 'https' or not url.hostname or url.username or url.query or url.fragment or url.path not in ('', '/'):
        parser.error('Usa solo la URL base HTTPS del backend.')
    print('Esta prueba vinculará permanentemente una licencia de PRUEBA al ID ficticio A. No uses una licencia destinada a un usuario.')
    key = getpass.getpass('KEY de prueba (entrada oculta): ').strip()
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *args, **kwargs):
            return None
    opener = urllib.request.build_opener(NoRedirect)
    for machine, expected in [('a'*64,'LICENSE_ACTIVATED'), ('a'*64,'LICENSE_ALREADY_ACTIVE_ON_THIS_DEVICE'), ('b'*64,'LICENSE_ALREADY_BOUND')]:
        req = urllib.request.Request(args.url.rstrip('/')+'/activate',
            data=json.dumps({'key': key, 'machine_id': machine}).encode(),
            headers={'Content-Type':'application/json'})
        try:
            try:
                response = opener.open(req, timeout=120)
            except urllib.error.HTTPError as exc:
                response = exc
            with response:
                data = json.load(response)
                code = data.get('code')
                print(f'HTTP {response.status}: {code} — esperado {expected}')
                if code != expected:
                    print('La prueba se detiene. Si la KEY ya estaba activada, genera otra exclusivamente para esta prueba.')
                    return 1
        except Exception:
            print('No se pudo completar la petición. Consulta el estado administrativo antes de repetir.')
            return 1
    print('PASS: activación, repetición en A y rechazo desde B.')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
