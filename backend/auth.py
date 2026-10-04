"""Authentication for Campus Customs: password hashing, verification, and JWT sessions.

Passwords are never stored in plaintext. We use PBKDF2-HMAC-SHA256 (a slow,
salted, standard-library KDF) with a per-user random salt and a high iteration
count. The stored string is self-describing:

    pbkdf2_sha256$<iterations>$<salt_hex>$<hash_hex>

This matches the existing `pbkdf2_sha256$...` convention in the users table while
also recording the iteration count, so hashes stay verifiable if we raise the
work factor later. Verification uses a constant-time comparison to avoid timing
attacks, and the hash is never exposed through any API response.
"""

import hashlib
import hmac
import os
import secrets
import time

import jwt

ALGORITHM = "pbkdf2_sha256"
ITERATIONS = 600_000           # OWASP-recommended floor for PBKDF2-SHA256 (2023+)
SALT_BYTES = 16
HASH_BYTES = 32                # 64 hex chars, matching the seed data

# The seed accounts (test, Ada, Tauhid) use a legacy 3-part format
# `pbkdf2_sha256$<salt>$<hash>` where the salt is a raw UTF-8 string and the
# work factor is fixed at 120,000 iterations. We verify those as-is and
# transparently upgrade them to the 4-part format on next login.
LEGACY_ITERATIONS = 120_000

# Secret for signing session tokens. Set CC_JWT_SECRET in the environment for a
# stable secret across restarts; otherwise a random one is generated per process.
JWT_SECRET = os.environ.get("CC_JWT_SECRET") or secrets.token_hex(32)
JWT_ALGO = "HS256"
TOKEN_TTL_SECONDS = 7 * 24 * 3600   # 7 days


def hash_password(password: str) -> str:
    """Return a self-describing PBKDF2 hash string for a new password."""
    salt = secrets.token_bytes(SALT_BYTES)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERATIONS, HASH_BYTES)
    return f"{ALGORITHM}${ITERATIONS}${salt.hex()}${dk.hex()}"


def verify_password(password: str, stored: str) -> bool:
    """Check a password against a stored hash, in constant time.

    Supports the 4-part format we write (with iterations) and is tolerant of a
    legacy 3-part `pbkdf2_sha256$salt$hash` form (assumes the default iteration
    count), so pre-existing rows don't crash the verifier.
    """
    try:
        parts = stored.split("$")
        if len(parts) == 4:
            # Our format: pbkdf2_sha256$<iterations>$<salt_hex>$<hash_hex>
            algo, iterations_str, salt_hex, hash_hex = parts
            if algo != ALGORITHM:
                return False
            iterations = int(iterations_str)
            salt = bytes.fromhex(salt_hex)
        elif len(parts) == 3:
            # Legacy seed format: pbkdf2_sha256$<salt>$<hash_hex>, where the
            # salt is a raw UTF-8 string and iterations are fixed at 120,000.
            algo, salt_str, hash_hex = parts
            if algo != ALGORITHM:
                return False
            iterations = LEGACY_ITERATIONS
            salt = salt_str.encode("utf-8")
        else:
            return False
        expected = bytes.fromhex(hash_hex)
    except (ValueError, AttributeError):
        return False

    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations, len(expected))
    return hmac.compare_digest(dk, expected)


def needs_rehash(stored: str) -> bool:
    """True if a stored hash uses the legacy format and should be upgraded."""
    return stored.count("$") == 2


def create_token(user_id: int) -> str:
    now = int(time.time())
    payload = {"sub": str(user_id), "iat": now, "exp": now + TOKEN_TTL_SECONDS}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)


def decode_token(token: str) -> int | None:
    """Return the user_id from a valid token, or None if invalid/expired."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
        return int(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError):
        return None
