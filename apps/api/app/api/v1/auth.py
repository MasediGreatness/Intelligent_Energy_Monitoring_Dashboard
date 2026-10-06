"""Login, logout, and current-user endpoints."""

from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth import (
    SESSION_COOKIE_NAME,
    create_session,
    current_auth_session,
    current_user,
    verify_password,
)
from app.core.config import get_settings
from app.core.errors import ApplicationError
from app.core.rate_limit import limiter
from app.db.session import get_db_session
from app.models import AuthSession, User
from app.schemas.auth import LoginRequest, LoginResponse, LogoutResponse, UserIdentity
from app.services.audit import record_audit_event

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])


@router.post("/login", response_model=LoginResponse)
@limiter.limit("10/minute")
def login(
    request: Request,
    credentials: LoginRequest,
    response: Response,
    session: Annotated[Session, Depends(get_db_session)],
) -> LoginResponse:
    user = session.scalar(select(User).where(User.email == credentials.email.lower()))
    password = credentials.password.get_secret_value()
    if (
        user is None
        or not user.is_active
        or not verify_password(user.password_hash, password)
    ):
        record_audit_event(
            session,
            event_type="auth.login_failed",
            details={"email": credentials.email.lower()},
        )
        session.commit()
        raise ApplicationError(
            status_code=401,
            code="INVALID_CREDENTIALS",
            message="The email or password is invalid.",
        )
    raw_token, auth_session = create_session(session, user)
    user.last_login_at = datetime.now(UTC)
    record_audit_event(
        session,
        event_type="auth.login_succeeded",
        actor_user_id=user.id,
        entity_type="user",
        entity_id=str(user.id),
    )
    session.commit()
    settings = get_settings()
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=raw_token,
        httponly=True,
        secure=settings.SESSION_COOKIE_SECURE,
        samesite="strict",
        max_age=settings.AUTH_SESSION_MINUTES * 60,
        path="/api/v1",
    )
    return LoginResponse(
        user=UserIdentity(id=user.id, email=user.email, role=user.role),
        expires_at=auth_session.expires_at,
    )


@router.post("/logout", response_model=LogoutResponse)
def logout(
    response: Response,
    session: Annotated[Session, Depends(get_db_session)],
    auth_session: Annotated[AuthSession, Depends(current_auth_session)],
    user: Annotated[User, Depends(current_user)],
) -> LogoutResponse:
    auth_session.revoked_at = datetime.now(UTC)
    record_audit_event(
        session,
        event_type="auth.logout",
        actor_user_id=user.id,
        entity_type="user",
        entity_id=str(user.id),
    )
    session.commit()
    response.delete_cookie(SESSION_COOKIE_NAME, path="/api/v1")
    return LogoutResponse()


@router.get("/me", response_model=UserIdentity)
def me(user: Annotated[User, Depends(current_user)]) -> UserIdentity:
    return UserIdentity(id=user.id, email=user.email, role=user.role)
