"""Password hashing helpers (bcrypt).

Uses the ``bcrypt`` library directly. bcrypt has a 72-byte input limit;
passwords are truncated to 72 bytes before hashing/verifying so longer inputs
don't raise. Demo passwords are far below this limit.
"""

from __future__ import annotations

import bcrypt

_MAX_BCRYPT_BYTES = 72


def _to_bytes(password: str) -> bytes:
    return password.encode("utf-8")[:_MAX_BCRYPT_BYTES]


def hash_password(password: str) -> str:
    """Return a bcrypt hash (utf-8 string) for the given password."""
    return bcrypt.hashpw(_to_bytes(password), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a plaintext password against a stored bcrypt hash."""
    try:
        return bcrypt.checkpw(_to_bytes(password), password_hash.encode("utf-8"))
    except ValueError:
        return False
