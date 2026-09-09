from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator

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

class ActivateRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', hide_input_in_errors=True)
    key: str = Field(min_length=19, max_length=19, pattern=r'^[A-Z2-9]{4}(-[A-Z2-9]{4}){3}$', repr=False)
    machine_id: str = Field(min_length=64, max_length=64, pattern=r'^[0-9a-f]{64}$')

    @field_validator('key', 'machine_id', mode='before')
    @classmethod
    def normalize(cls, value, info):
        if isinstance(value, str):
            return value.strip().upper() if info.field_name == 'key' else value.strip().lower()
        return value

class ActivationResult(BaseModel):
    code: str
    license_id: str
    product_id: str
    token: str
    signature: str
