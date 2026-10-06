"""Authentication request and response contracts."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, SecretStr

from app.models.enums import UserRole


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: SecretStr = Field(min_length=12, max_length=256)


class UserIdentity(BaseModel):
    id: UUID
    email: EmailStr
    role: UserRole


class LoginResponse(BaseModel):
    user: UserIdentity
    expires_at: datetime


class LogoutResponse(BaseModel):
    status: str = "logged_out"
