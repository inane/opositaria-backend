"""Stubs and spies for application ports used in unit tests."""


class StubPasswordHasher:
    """Deterministic stub for PasswordHasher used in unit tests.

    Instead of actually hashing, it wraps the password in a recognizable
    format so that tests can verify the hash was produced and verified.
    """

    def hash(self, plain_password: str) -> str:
        """Return a deterministic fake hash."""
        return f"hashed:{plain_password}"

    def verify(self, plain_password: str, password_hash: str) -> bool:
        """Verify by checking the fake hash format."""
        return password_hash == f"hashed:{plain_password}"


class SpyTokenService:
    """Spy for TokenService that records issued tokens and validates them."""

    def __init__(self) -> None:
        self._issued_tokens: dict[str, str] = {}

    def issue_token(self, user_id: str) -> str:
        """Issue a deterministic token for a user id."""
        token = f"token:{user_id}"
        self._issued_tokens[token] = user_id
        return token

    def validate_token(self, token: str) -> str | None:
        """Validate a token and return the user id if valid."""
        return self._issued_tokens.get(token)
