"""Password hashing utilities using bcrypt."""

from __future__ import annotations

import bcrypt


class PasswordHasher:
    """Hash and verify passwords securely."""

    def hash_password(self, plain_password: str) -> str:
        """Return a bcrypt hash for the given password."""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(plain_password.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Return True when the password matches the hash."""
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
