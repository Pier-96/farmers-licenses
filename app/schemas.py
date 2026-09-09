from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class CreateLicense(BaseModel):
    model_config = ConfigDict(extra='forbid')
    product_id: str = Field(default='multicliente', pattern=r'^[a-z0-9_-]{1,64}$')
    max_activations: int = Field(default=1, ge=1, le=1000, strict=True)
    notes: str | None = Field(default=None, max_length=2000)

class LicenseView(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    product_id: str
    key_prefix: str
    status: str
    machine_id: str | None
    created_at: datetime
    activated_at: datetime | None
    last_validation_at: datetime | None
    activation_count: int
    max_activations: int
    revoked_at: datetime | None
    notes: str | None

class IssuedLicense(BaseModel):
    key: str
    license: LicenseView
