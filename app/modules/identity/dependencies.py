import uuid

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.infrastructure.database.session import get_db
from app.modules.identity.models import User, UserStatus
from app.modules.identity.security import decode_token

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    payload = decode_token(credentials.credentials)
    if payload.get("type") != "access":
        raise AppError("Invalid access token", status_code=401)

    try:
        user_id = uuid.UUID(payload.get("sub", ""))
    except ValueError:
        raise AppError("Invalid access token", status_code=401) from None

    user = await db.get(User, user_id)
    if user is None or user.status != UserStatus.ACTIVE:
        raise AppError("Invalid access token", status_code=401)
    return user
