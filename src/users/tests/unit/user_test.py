"""Unit tests for User domain entity."""

import uuid
from datetime import datetime

from src.users.domain.entities import User, UserError


class TestUser:
    """Tests for the User domain entity."""

    def test_creates_user_with_required_fields(self) -> None:
        """A user is created with id, email, password_hash, and timestamps."""
        user_id = uuid.uuid4()
        email = "student@example.com"
        password_hash = "$2b$12$hashedpassword123"

        user = User.create(
            id=user_id,
            email=email,
            password_hash=password_hash,
        )

        assert user.id == user_id
        assert user.email == email
        assert user.password_hash == password_hash
        assert isinstance(user.created_at, datetime)
        assert isinstance(user.updated_at, datetime)
        assert user.created_at is not None
        assert user.updated_at is not None

    def test_public_data_excludes_password_hash(self) -> None:
        """User public representation does not include password_hash."""
        user_id = uuid.uuid4()
        email = "student@example.com"
        password_hash = "$2b$12$hashedpassword123"

        user = User.create(
            id=user_id,
            email=email,
            password_hash=password_hash,
        )

        public = user.to_public_dict()
        assert "password_hash" not in public
        assert public["id"] == str(user_id)
        assert public["email"] == email
        assert "created_at" in public
        assert "updated_at" in public


class TestUserError:
    """Tests for UserError domain error."""

    def test_creates_with_message_and_code(self) -> None:
        """UserError is created with a message and an error code."""
        error = UserError("Email already registered", code="duplicate_email")
        assert error.message == "Email already registered"
        assert error.code == "duplicate_email"
        assert str(error) == "Email already registered"
