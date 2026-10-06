"""Opaque, revocable session authentication and role dependencies."""

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from secrets import token_urlsafe
from typing import Annotated

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError
from fastapi import Depends, Security
from fastapi.security import APIKeyCookie
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import ApplicationError
from app.db.session import get_db_session
from app.models import AuthSession, User
from app.models.enums import UserRole

password_hasher = PasswordHasher()
SESSION_COOKIE_NAME = "energy_session"
session_cookie = APIKeyCookie(name=SESSION_COOKIE_NAME, auto_error=False)


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return password_hasher.verify(password_hash, password)
    except (VerifyMismatchError, InvalidHashError):
        return False


def _token_hash(token: str) -> str:
    return sha256(token.encode("utf-8")).hexdigest()


def create_session(session: Session, user: User) -> tuple[str, AuthSession]:
    raw_token = token_urlsafe(48)
    expires_at = datetime.now(UTC) + timedelta(
        minutes=get_settings().AUTH_SESSION_MINUTES
    )
    auth_session = AuthSession(
        user_id=user.id,
        token_hash=_token_hash(raw_token),
        expires_at=expires_at,
    )
    session.add(auth_session)
    session.flush()
    return raw_token, auth_session


def current_auth_session(
    session: Annotated[Session, Depends(get_db_session)],
    token: Annotated[str | None, Security(session_cookie)],
) -> AuthSession:
    return authenticate_token(session, token)


def authenticate_token(session: Session, token: str | None) -> AuthSession:
    if token is None:
        raise ApplicationError(
            status_code=401,
            code="AUTHENTICATION_REQUIRED",
            message="Authentication is required.",
        )
    auth_session = session.scalar(
        select(AuthSession).where(AuthSession.token_hash == _token_hash(token))
    )
    now = datetime.now(UTC)
    if (
        auth_session is None
        or auth_session.revoked_at is not None
        or auth_session.expires_at <= now
    ):
        raise ApplicationError(
            status_code=401,
            code="SESSION_EXPIRED",
            message="The authentication session is invalid or expired.",
        )
    return auth_session


def current_user(
    session: Annotated[Session, Depends(get_db_session)],
    auth_session: Annotated[AuthSession, Depends(current_auth_session)],
) -> User:
    user = session.get(User, auth_session.user_id)
    if user is None or not user.is_active:
        raise ApplicationError(
            status_code=401,
            code="AUTHENTICATION_REQUIRED",
            message="Authentication is required.",
        )
    return user


def require_roles(*roles: UserRole) -> Callable[..., User]:
    def dependency(user: Annotated[User, Depends(current_user)]) -> User:
        if user.role not in roles:
            raise ApplicationError(
                status_code=403,
                code="INSUFFICIENT_PERMISSION",
                message="The current role cannot perform this action.",
            )
        return user

    return dependency
