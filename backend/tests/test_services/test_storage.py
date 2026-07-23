import pytest

from app.config import settings
from app.services.storage import (
    FileTooLargeError,
    LocalStorage,
    sanitize_filename,
)


def test_sanitize_strips_path_traversal():
    assert sanitize_filename("../../etc/passwd") == "passwd"
    assert sanitize_filename("/abs/path/report.pdf") == "report.pdf"
    assert sanitize_filename("weird name!.pdf") == "weird_name_.pdf"
    assert sanitize_filename("") == "upload.bin"
    assert sanitize_filename("...") == "upload.bin"


def test_save_and_read_round_trip(tmp_path):
    storage = LocalStorage(base_dir=str(tmp_path))
    rel = storage.build_path("documents", "pa-123", "note.txt")
    size = storage.save(rel, b"clinical bytes")
    assert size == len("clinical bytes")
    assert storage.exists(rel) is True
    assert storage.read(rel) == b"clinical bytes"


def test_build_path_ignores_client_directories(tmp_path):
    storage = LocalStorage(base_dir=str(tmp_path))
    rel = storage.build_path("documents", "pa-123", "../../escape.txt")
    storage.save(rel, b"x")
    # The stored file stays under base_dir despite the malicious filename.
    written = list(tmp_path.rglob("*.txt"))
    assert len(written) == 1
    assert tmp_path in written[0].parents


def test_save_rejects_oversize(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "max_upload_bytes", 10)
    storage = LocalStorage(base_dir=str(tmp_path))
    rel = storage.build_path("documents", "pa-1", "big.bin")
    with pytest.raises(FileTooLargeError):
        storage.save(rel, b"0123456789A")
