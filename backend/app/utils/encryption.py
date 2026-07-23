import base64

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from sqlalchemy import String, Text
from sqlalchemy.types import TypeDecorator

from app.config import settings

# Fernet derivation is ~100k PBKDF2 rounds; deriving it per field would dominate
# request latency, so we build it once and reuse it for the process lifetime.
_fernet: Fernet | None = None


def _get_fernet() -> Fernet:
    """Derive (once) a Fernet key from the configured encryption key and salt."""
    global _fernet
    if _fernet is None:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=settings.encryption_salt.encode(),
            iterations=100_000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(settings.encryption_key.encode()))
        _fernet = Fernet(key)
    return _fernet


def encrypt_phi(plaintext: str) -> str:
    """Encrypt a PHI field value. Empty/None passes through unchanged."""
    if not plaintext:
        return plaintext
    return _get_fernet().encrypt(plaintext.encode()).decode()


def decrypt_phi(ciphertext: str) -> str:
    """
    Decrypt a PHI field value.

    Falls back to returning the value unchanged if it isn't a valid Fernet
    token — this lets us read rows written before column encryption was enabled
    without a destructive backfill.
    """
    if not ciphertext:
        return ciphertext
    try:
        return _get_fernet().decrypt(ciphertext.encode()).decode()
    except (InvalidToken, ValueError):
        return ciphertext


class EncryptedString(TypeDecorator):
    """
    Column type that encrypts PHI at rest with Fernet.

    Values are encrypted on the way into the database and decrypted on the way
    out, so application code and API schemas see plaintext. Ciphertext is stored
    as text (Fernet tokens are base64 and longer than the plaintext), so do NOT
    use this for columns that need SQL search/indexing — the stored value is
    opaque. Legacy plaintext rows are returned as-is (see decrypt_phi).
    """

    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        return encrypt_phi(str(value))

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        return decrypt_phi(value)
