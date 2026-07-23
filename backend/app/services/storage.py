"""
File storage for uploaded documents.

LocalStorage writes to a directory on the local filesystem. This is real,
working storage for local/dev and any deploy with a persistent volume, but it is
NOT durable on Railway's ephemeral filesystem — swap in an S3-backed
implementation with the same interface for production PHI retention.
"""
import os
import re
import uuid
from pathlib import Path

from app.config import settings


class FileTooLargeError(Exception):
    """Raised when an upload exceeds settings.max_upload_bytes."""


_SAFE_NAME = re.compile(r"[^A-Za-z0-9._-]")


def sanitize_filename(name: str | None) -> str:
    """Strip path separators and unsafe characters to prevent path traversal."""
    base = os.path.basename(name or "").strip()
    base = _SAFE_NAME.sub("_", base)
    # Guard against names that sanitize to nothing or to dot-only sequences.
    if not base or set(base) <= {"."}:
        return "upload.bin"
    return base[:255]


class LocalStorage:
    """Persist and retrieve files under settings.upload_dir."""

    def __init__(self, base_dir: str | None = None):
        self.base_dir = Path(base_dir or settings.upload_dir)

    def _abs(self, rel_path: str) -> Path:
        # Resolve and confirm the target stays within base_dir.
        base = self.base_dir.resolve()
        target = (base / rel_path).resolve()
        if base != target and base not in target.parents:
            raise ValueError("Resolved path escapes the storage directory")
        return target

    def build_path(self, prefix: str, entity_id: str, filename: str) -> str:
        """Server-generated relative path — never trust client-supplied paths."""
        safe = sanitize_filename(filename)
        return f"{prefix}/{entity_id}/{uuid.uuid4()}/{safe}"

    def save(self, rel_path: str, content: bytes) -> int:
        if len(content) > settings.max_upload_bytes:
            raise FileTooLargeError(
                f"Upload is {len(content)} bytes; limit is {settings.max_upload_bytes}"
            )
        target = self._abs(rel_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        return len(content)

    def read(self, rel_path: str) -> bytes:
        return self._abs(rel_path).read_bytes()

    def exists(self, rel_path: str) -> bool:
        return self._abs(rel_path).is_file()


def get_storage() -> LocalStorage:
    """FastAPI dependency / factory for the active storage backend."""
    return LocalStorage()
