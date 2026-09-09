from alembic import context
from app.config import Settings
from app.database import build_engine, Base
from app import models

engine = build_engine(Settings())
with engine.connect() as connection:
    context.configure(connection=connection, target_metadata=Base.metadata)
    with context.begin_transaction():
        context.run_migrations()
engine.dispose()
