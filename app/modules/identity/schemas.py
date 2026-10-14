import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator


class RegisterRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    first_name: str = Field(alias="firstName", min_length=1, max_length=100)
    last_name: str = Field(alias="lastName", min_length=1, max_length=100)
    email: EmailStr
    mobile: str = Field(min_length=8, max_length=20)
    password: str = Field(min_length=8, max_length=72)

    @field_validator("first_name", "last_name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("must not be blank")
        return cleaned

    @field_validator("mobile")
    @classmethod
    def normalize_mobile(cls, value: str) -> str:
        return normalize_mobile_number(value)


def normalize_mobile_number(value: str) -> str:
    cleaned = "".join(value.split())
    digits = cleaned[1:] if cleaned.startswith("+") else cleaned
    if not digits.isdigit() or not 8 <= len(digits) <= 15:
        raise ValueError("must be 8 to 15 digits, with an optional leading +")
    return cleaned


class LoginRequest(BaseModel):
    email: EmailStr | None = None
    mobile: str | None = None
    password: str = Field(min_length=8, max_length=72)

    @field_validator("mobile")
    @classmethod
    def normalize_mobile(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return normalize_mobile_number(value)

    @model_validator(mode="after")
    def require_email_or_mobile(self) -> "LoginRequest":
        if self.email is None and self.mobile is None:
            raise ValueError("email or mobile is required")
        return self


class RefreshRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    refresh_token: str = Field(alias="refreshToken", min_length=1)


class TokenResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    access_token: str = Field(alias="accessToken")
    refresh_token: str = Field(alias="refreshToken")
    token_type: str = Field(alias="tokenType", default="bearer")
    access_token_expires_in: int = Field(alias="accessTokenExpiresIn")


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: uuid.UUID
    first_name: str = Field(alias="firstName")
    last_name: str = Field(alias="lastName")
    email: EmailStr
    mobile: str
    status: str
    email_verified: bool = Field(alias="emailVerified")
    mobile_verified: bool = Field(alias="mobileVerified")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")
    last_login_at: datetime | None = Field(alias="lastLoginAt")
