"""Explicit, idempotent user setup with an environment or interactive password."""

import argparse
import getpass
import os

from pydantic import EmailStr, TypeAdapter, ValidationError
from sqlalchemy import select

from app.core.auth import hash_password
from app.db.session import get_session_factory
from app.models import User
from app.models.enums import UserRole

EMAIL_ADAPTER = TypeAdapter(EmailStr)


def normalize_email(value: str) -> str:
    """Apply the same email contract used by the login API."""

    try:
        return str(EMAIL_ADAPTER.validate_python(value.strip().lower()))
    except ValidationError as exc:
        raise SystemExit("Email must be a valid address.") from exc


def main() -> None:
    parser = argparse.ArgumentParser(description="Create or update a dashboard user")
    parser.add_argument("--email", required=True)
    parser.add_argument(
        "--role", choices=[item.value for item in UserRole], required=True
    )
    args = parser.parse_args()
    password = os.environ.get("ENERGY_SETUP_PASSWORD") or getpass.getpass(
        "Password (minimum 12 characters): "
    )
    if len(password) < 12:
        raise SystemExit("Password must contain at least 12 characters.")
    email = normalize_email(args.email)
    with get_session_factory()() as session:
        user = session.scalar(select(User).where(User.email == email))
        if user is None:
            user = User(
                email=email,
                password_hash=hash_password(password),
                role=UserRole(args.role),
            )
            session.add(user)
        else:
            user.password_hash = hash_password(password)
            user.role = UserRole(args.role)
            user.is_active = True
        session.commit()
        print(f"Configured {email} as {user.role.value}.")


if __name__ == "__main__":
    main()
