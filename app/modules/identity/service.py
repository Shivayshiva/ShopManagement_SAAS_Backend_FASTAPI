from datetime import UTC, datetime

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.modules.identity.models import RefreshToken, User, UserStatus
from app.modules.identity.schemas import LoginRequest, RegisterRequest, TokenResponse
from app.modules.identity.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_token,
    verify_password,
)


async def register_user(db: AsyncSession, payload: RegisterRequest) -> User:
    email = payload.email.lower()
    mobile = payload.mobile

    result = await db.execute(
        select(User).where(or_(User.email == email, User.mobile == mobile))
    )
    existing = result.scalars().all()
    email_taken = any(user.email == email for user in existing)
    mobile_taken = any(user.mobile == mobile for user in existing)
    if email_taken and mobile_taken:
        raise AppError(
            "A user with this email and mobile number already exists",
            status_code=409,
        )
    if email_taken:
        raise AppError("A user with this email already exists", status_code=409)
    if mobile_taken:
        raise AppError("A user with this mobile number already exists", status_code=409)

    now = datetime.now(UTC)
    user = User(
        first_name=payload.first_name,
        last_name=payload.last_name,
        email=email,
        mobile=mobile,
        password_hash=hash_password(payload.password),
        status=UserStatus.ACTIVE,
        email_verified=False,
        mobile_verified=False,
        created_at=now,
        updated_at=now,
        last_login_at=None,
    )
    db.add(user)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise AppError(
            "A user with this email or mobile number already exists",
            status_code=409,
        ) from None
    await db.refresh(user)
    return user


async def _issue_tokens(db: AsyncSession, user: User) -> TokenResponse:
    access_token, expires_in = create_access_token(user.id)
    refresh_token, expires_at = create_refresh_token(user.id)
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_token(refresh_token),
            expires_at=expires_at,
            revoked_at=None,
            created_at=datetime.now(UTC),
        )
    )
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        access_token_expires_in=expires_in,
    )


async def _get_valid_refresh_token(db: AsyncSession, raw_token: str) -> tuple[RefreshToken, User]:
    payload = decode_token(raw_token)
    if payload.get("type") != "refresh":
        raise AppError("Invalid refresh token", status_code=401)

    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == hash_token(raw_token))
    )
    stored = result.scalar_one_or_none()
    now = datetime.now(UTC)
    if stored is None or stored.revoked_at is not None or stored.expires_at <= now:
        raise AppError("Invalid refresh token", status_code=401)
    if str(stored.user_id) != payload.get("sub"):
        raise AppError("Invalid refresh token", status_code=401)

    user = await db.get(User, stored.user_id)
    if user is None or user.status != UserStatus.ACTIVE:
        raise AppError("Invalid refresh token", status_code=401)
    return stored, user


async def login_user(db: AsyncSession, payload: LoginRequest) -> TokenResponse:
    filters = []
    if payload.email is not None:
        filters.append(User.email == payload.email.lower())
    if payload.mobile is not None:
        filters.append(User.mobile == payload.mobile)

    result = await db.execute(select(User).where(*filters))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise AppError("Invalid email, mobile, or password", status_code=401)
    if user.status != UserStatus.ACTIVE:
        raise AppError("Account is not active", status_code=403)

    now = datetime.now(UTC)
    user.last_login_at = now
    user.updated_at = now
    tokens = await _issue_tokens(db, user)
    await db.commit()
    return tokens


async def refresh_session(db: AsyncSession, refresh_token: str) -> TokenResponse:
    stored, user = await _get_valid_refresh_token(db, refresh_token)
    stored.revoked_at = datetime.now(UTC)
    tokens = await _issue_tokens(db, user)
    await db.commit()
    return tokens


async def logout_user(db: AsyncSession, user: User, refresh_token: str) -> None:
    stored, token_user = await _get_valid_refresh_token(db, refresh_token)
    if token_user.id != user.id:
        raise AppError("Invalid refresh token", status_code=401)
    stored.revoked_at = datetime.now(UTC)
    await db.commit()
