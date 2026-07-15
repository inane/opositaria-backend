"""Unit tests for user value objects."""

import pytest

from src.users.domain.value_objects import (
    normalize_email,
    EmailAddress,
    PlainPassword,
)


class TestNormalizeEmail:
    """Tests for email normalization function."""

    def test_lowercases_email(self) -> None:
        """Email is lowercased during normalization."""
        result = normalize_email("Student@Example.com")
        assert result == "student@example.com"

    def test_trims_whitespace(self) -> None:
        """Surrounding whitespace is trimmed during normalization."""
        result = normalize_email("  student@example.com  ")
        assert result == "student@example.com"

    def test_handles_mixed_case_with_whitespace(self) -> None:
        """Mixed case and whitespace are both normalized."""
        result = normalize_email("  Student@Example.COM  ")
        assert result == "student@example.com"


class TestEmailAddress:
    """Tests for EmailAddress value object."""

    def test_creates_from_normalized_email(self) -> None:
        """EmailAddress is created from a valid email string."""
        email = EmailAddress("student@example.com")
        assert email.value == "student@example.com"

    def test_normalizes_on_creation(self) -> None:
        """EmailAddress normalizes the email on construction."""
        email = EmailAddress("  Student@Example.COM  ")
        assert email.value == "student@example.com"

    def test_equality_based_on_normalized_value(self) -> None:
        """Two EmailAddress instances with the same normalized email are equal."""
        email1 = EmailAddress("student@example.com")
        email2 = EmailAddress("  Student@Example.COM  ")
        assert email1 == email2
        assert hash(email1) == hash(email2)

    def test_rejects_email_without_at_sign(self) -> None:
        """EmailAddress rejects an email missing the @ symbol."""
        with pytest.raises(ValueError, match="Invalid email address"):
            EmailAddress("notanemail")

    def test_rejects_email_without_domain(self) -> None:
        """EmailAddress rejects an email missing a domain after @."""
        with pytest.raises(ValueError, match="Invalid email address"):
            EmailAddress("user@")

    def test_rejects_email_without_local_part(self) -> None:
        """EmailAddress rejects an email missing a local part before @."""
        with pytest.raises(ValueError, match="Invalid email address"):
            EmailAddress("@domain.com")


class TestPlainPassword:
    """Tests for PlainPassword value object."""

    def test_creates_password_with_minimum_length(self) -> None:
        """PlainPassword accepts a password with the minimum required length."""
        password = PlainPassword("password")
        assert password.value == "password"

    def test_rejects_password_below_minimum_length(self) -> None:
        """PlainPassword rejects a password shorter than the minimum length."""
        with pytest.raises(ValueError, match="Password must be at least"):
            PlainPassword("short")
