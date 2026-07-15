"""Unit tests for security adapters (password hashing and JWT)."""

import uuid


from src.users.infrastructure.security import BcryptPasswordHasher, JwtTokenService


class TestBcryptPasswordHasher:
    """Tests for BcryptPasswordHasher."""

    def test_hash_does_not_equal_plain_password(self) -> None:
        """A hashed password is different from the plain password."""
        hasher = BcryptPasswordHasher()
        password = "password123"

        hashed = hasher.hash(password)

        assert hashed != password
        assert hashed.startswith("$2b$")

    def test_verifies_correct_password(self) -> None:
        """A correct password is verified against its hash."""
        hasher = BcryptPasswordHasher()
        password = "password123"
        hashed = hasher.hash(password)

        assert hasher.verify(password, hashed) is True

    def test_rejects_incorrect_password(self) -> None:
        """An incorrect password is rejected."""
        hasher = BcryptPasswordHasher()
        hashed = hasher.hash("password123")

        assert hasher.verify("wrongpassword", hashed) is False


class TestJwtTokenService:
    """Tests for JwtTokenService."""

    def test_issues_token_with_user_subject(self) -> None:
        """A JWT token is issued with the user id as subject."""
        token_service = JwtTokenService()
        user_id = str(uuid.uuid4())

        token = token_service.issue_token(user_id)

        assert token is not None
        assert isinstance(token, str)
        # Token should have two dots (JWT format: header.payload.signature)
        assert token.count(".") == 2

    def test_validates_token_and_returns_subject(self) -> None:
        """A valid token returns the user id."""
        token_service = JwtTokenService()
        user_id = str(uuid.uuid4())

        token = token_service.issue_token(user_id)
        subject = token_service.validate_token(token)

        assert subject == user_id

    def test_rejects_invalid_token(self) -> None:
        """An invalid or malformed token returns None."""
        token_service = JwtTokenService()

        assert token_service.validate_token("invalid-token") is None
        assert token_service.validate_token("") is None
        assert token_service.validate_token("a.b.c") is None
