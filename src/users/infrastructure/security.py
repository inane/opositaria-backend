"""Security adapters for password hashing and JWT token management."""

from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from src.shared.infrastructure.settings import AuthSettings


class BcryptPasswordHasher:
    """Password hasher using bcrypt."""

    def hash(self, plain_password: str) -> str:
        """Hash a plain password using bcrypt."""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(plain_password.encode("utf-8"), salt).decode("utf-8")

    def verify(self, plain_password: str, password_hash: str) -> bool:
        """Verify a plain password against a bcrypt hash."""
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), password_hash.encode("utf-8")
        )


class JwtTokenService:
    """JWT token service for issuing and validating access tokens."""

    def __init__(self, settings: AuthSettings | None = None) -> None:
        self._settings = settings or AuthSettings()

    def issue_token(self, user_id: str) -> str:
        """Issue a JWT access token for the given user."""
        now = datetime.now(timezone.utc)
        payload = {
            "sub": user_id,
            "iat": now,
            "exp": now
            + timedelta(minutes=self._settings.jwt_access_token_expire_minutes),
        }
        return jwt.encode(
            payload,
            self._settings.jwt_secret_key,
            algorithm=self._settings.jwt_algorithm,
        )

    def validate_token(self, token: str) -> str | None:
        """Validate a JWT token and return the user subject.

        Returns the user id as a string if valid, None otherwise.
        """
        try:
            payload = jwt.decode(
                token,
                self._settings.jwt_secret_key,
                algorithms=[self._settings.jwt_algorithm],
            )
            return payload.get("sub")
        except jwt.PyJWTError:
            return None
