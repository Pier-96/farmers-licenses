from datetime import datetime
from sqlalchemy import String, Integer, DateTime, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base

class License(Base):
    __tablename__ = 'licenses'
    __table_args__ = (
        CheckConstraint("status IN ('unused','active','revoked')", name='license_status'),
        CheckConstraint('activation_count >= 0 AND max_activations >= 1', name='activation_limits'),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    product_id: Mapped[str] = mapped_column(String(64), index=True)
    key_hash: Mapped[str] = mapped_column(String(64), unique=True)
    key_prefix: Mapped[str] = mapped_column(String(4))
    status: Mapped[str] = mapped_column(String(16), default='unused')
    machine_id: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_validation_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    activation_count: Mapped[int] = mapped_column(Integer, default=0)
    max_activations: Mapped[int] = mapped_column(Integer, default=1)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str | None] = mapped_column(String(2000))
