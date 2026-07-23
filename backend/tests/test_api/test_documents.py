import uuid

import pytest
from httpx import AsyncClient

from app.config import settings
from app.services.storage import LocalStorage


@pytest.fixture
def _tmp_uploads(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path))
    return tmp_path


@pytest.mark.asyncio
async def test_upload_then_download_round_trip(client: AsyncClient, _tmp_uploads):
    pa_id = str(uuid.uuid4())
    resp = await client.post(
        "/api/v1/documents/upload",
        data={"prior_auth_id": pa_id, "document_type": "clinical_note"},
        files={"file": ("note.txt", b"the clinical bytes", "text/plain")},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["file_size"] == len("the clinical bytes")
    doc_id = body["document_id"]

    dl = await client.get(f"/api/v1/documents/{doc_id}/download")
    assert dl.status_code == 200
    assert dl.content == b"the clinical bytes"
    assert "attachment" in dl.headers["content-disposition"]


@pytest.mark.asyncio
async def test_download_missing_bytes_returns_404(client: AsyncClient, _tmp_uploads, db_session):
    # A DB row whose file was never written (e.g. legacy row) should 404, not 500.
    from app.models.clinical_document import ClinicalDocument

    doc = ClinicalDocument(
        id=str(uuid.uuid4()),
        prior_auth_id=str(uuid.uuid4()),
        document_type="clinical_note",
        file_name="ghost.txt",
        file_path="documents/ghost/ghost.txt",
    )
    db_session.add(doc)
    await db_session.commit()

    dl = await client.get(f"/api/v1/documents/{doc.id}/download")
    assert dl.status_code == 404
