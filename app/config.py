from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url

class Settings(BaseSettings):
    database_url: SecretStr
    admin_token: SecretStr
    model_config = SettingsConfigDict(env_file=None, extra='ignore', hide_input_in_errors=True)

    @model_validator(mode='after')
    def check(self):
        token = self.admin_token.get_secret_value()
        if len(token) < 32 or token.startswith('REPLACE_'):
            raise ValueError('ADMIN_TOKEN debe contener al menos 32 caracteres aleatorios.')
        try:
            url = make_url(self.database_url.get_secret_value())
            valid = url.get_backend_name() in ('postgres', 'postgresql')
        except Exception:
            valid = False
        if not valid:
            raise ValueError('DATABASE_URL debe ser una URL PostgreSQL válida.')
        return self

    def sqlalchemy_url(self):
        return make_url(self.database_url.get_secret_value()).set(drivername='postgresql+psycopg')
