import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.security import UserRole


class UserBase(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    full_name: str = Field(min_length=1, max_length=255)
    role: UserRole
    company_id: uuid.UUID | None = None
    phone: str = Field(min_length=1, max_length=255)


class UserCreate(UserBase):
    password: str = Field(min_length=6, max_length=128)
    id: uuid.UUID | None = None


class UserUpdate(BaseModel):
    full_name: str | None = None
    role: UserRole | None = None
    phone: str | None = None
    is_active: bool | None = None
    password: str | None = Field(default=None, min_length=6, max_length=128)


class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    is_active: bool
    created_at: datetime


class MeResponse(UserRead):
    pass
