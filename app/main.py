import secrets
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, Query, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy import select, text
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from .config import Settings
from .database import build_engine
from .models import License
from .schemas import CreateLicense, LicenseView, IssuedLicense, ActivateRequest, ActivationResult
from .activation import activate, ActivationDenied
from .licenses import issue
from .signing import Signer

def create_app(settings=None):
    settings = settings or Settings()
    signer = Signer(settings.private_signing_key.get_secret_value())
    engine = build_engine(settings)
    @asynccontextmanager
    async def lifespan(app):
        yield
        engine.dispose()
    app = FastAPI(title='Multicliente Licencias — Fase 5', docs_url=None,
                  redoc_url=None, openapi_url=None, lifespan=lifespan)
    bearer = HTTPBearer(auto_error=False)
    def admin(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)):
        if credentials is None or not secrets.compare_digest(
                credentials.credentials.encode(), settings.admin_token.get_secret_value().encode()):
            raise HTTPException(401, 'No autorizado', headers={'WWW-Authenticate': 'Bearer'})
    def database():
        with Session(engine) as session:
            yield session
    @app.middleware('http')
    async def no_cache(request, call_next):
        response = await call_next(request)
        response.headers['Cache-Control'] = 'no-store'
        return response
    @app.exception_handler(RequestValidationError)
    async def invalid(request, exc):
        return JSONResponse(status_code=422, content={'detail': 'Datos de solicitud inválidos.'})
    @app.exception_handler(SQLAlchemyError)
    async def db_error(request, exc):
        return JSONResponse(status_code=503, content={'detail': 'Base de datos no disponible.'})
    @app.exception_handler(Exception)
    async def unexpected(request, exc):
        return JSONResponse(status_code=500, content={'detail': 'Error interno.'})
    @app.get('/health')
    def health(session: Session = Depends(database)):
        session.execute(text('SELECT 1'))
        return {'status': 'ok', 'phase': 5}
    @app.get('/public-key')
    def public_key():
        return {'algorithm':'Ed25519', 'key_id':signer.key_id, 'public_key':signer.public}
    @app.post('/activate', response_model=ActivationResult)
    def activation(body: ActivateRequest, session: Session = Depends(database)):
        try:
            result = activate(session, body)
            result.update(signer.sign(result['license_id'], result['product_id'], body.machine_id))
            return result
        except ActivationDenied as exc:
            return JSONResponse(status_code=exc.status, content={'code': exc.code})
    @app.get('/licenses', response_model=list[LicenseView], dependencies=[Depends(admin)])
    def listing(limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0),
                session: Session = Depends(database)):
        return session.scalars(select(License).order_by(License.created_at, License.id).offset(offset).limit(limit)).all()
    @app.post('/admin/licenses', response_model=IssuedLicense, status_code=201,
              dependencies=[Depends(admin)])
    def create(body: CreateLicense, session: Session = Depends(database)):
        key, row = issue(session, body)
        return {'key': key, 'license': row}
    return app
