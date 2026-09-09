from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

def build_engine(settings):
    return create_engine(settings.sqlalchemy_url(), pool_pre_ping=True,
                         pool_size=2, max_overflow=1, hide_parameters=True,
                         connect_args={'connect_timeout': 10})
