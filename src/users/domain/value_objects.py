"""Value objects for user domain."""

MIN_PASSWORD_LENGTH = 8


def normalize_email(email: str) -> str:
    """Normalize an email address by trimming whitespace and lowercasing."""
    return email.strip().lower()


class EmailAddress:
    """An immutable email address value object.

    The email is normalized on construction so that case and whitespace
    variants of the same address compare as equal.
    """

    def __init__(self, email: str) -> None:
        normalized = normalize_email(email)
        self._validate(normalized)
        self._value = normalized

    @staticmethod
    def _validate(email: str) -> None:
        """Validate that the email has a basic valid structure."""
        if "@" not in email:
            raise ValueError("Invalid email address")
        local_part, _, domain = email.partition("@")
        if not local_part or not domain:
            raise ValueError("Invalid email address")

    @property
    def value(self) -> str:
        """Return the normalized email address."""
        return self._value

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, EmailAddress):
            return NotImplemented
        return self._value == other._value

    def __hash__(self) -> int:
        return hash(self._value)

    def __str__(self) -> str:
        return self._value


class PlainPassword:
    """An immutable plain-text password value object.

    Validates that the password meets the minimum length requirement.
    Never stored — only used during registration and login to
    compute the password hash.
    """

    def __init__(self, password: str) -> None:
        self._validate(password)
        self._value = password

    @staticmethod
    def _validate(password: str) -> None:
        """Validate that the password meets requirements."""
        if len(password) < MIN_PASSWORD_LENGTH:
            raise ValueError(
                f"Password must be at least {MIN_PASSWORD_LENGTH} characters long"
            )

    @property
    def value(self) -> str:
        """Return the plain password value."""
        return self._value
