import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.clinical_document import ClinicalDocument
from app.services.audit_service import AuditContext, get_audit_context

router = APIRouter()


@router.post("/upload")
async def upload_document(
    prior_auth_id: str = Form(...),
    document_type: str = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Upload a clinical document for a PA case."""
    doc_id = str(uuid.uuid4())
    file_path = f"uploads/documents/{prior_auth_id}/{doc_id}/{file.filename}"

    doc = ClinicalDocument(
        id=doc_id,
        prior_auth_id=prior_auth_id,
        document_type=document_type,
        file_name=file.filename,
        file_path=file_path,
        file_size=file.size,
        mime_type=file.content_type,
    )
    db.add(doc)
    await db.commit()

    return {
        "document_id": doc_id,
        "file_name": file.filename,
        "status": "uploaded",
        "message": f"Document uploaded for PA {prior_auth_id}",
    }


@router.get("", response_model=list[dict])
async def list_documents(
    prior_auth_id: str = None,
    document_type: str = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(ClinicalDocument)
    if prior_auth_id:
        stmt = stmt.where(ClinicalDocument.prior_auth_id == prior_auth_id)
    if document_type:
        stmt = stmt.where(ClinicalDocument.document_type == document_type)

    result = await db.execute(stmt)
    docs = result.scalars().all()
    return [
        {
            "id": d.id,
            "prior_auth_id": d.prior_auth_id,
            "document_type": d.document_type,
            "file_name": d.file_name,
            "file_size": d.file_size,
            "created_at": str(d.created_at),
        }
        for d in docs
    ]


@router.get("/{doc_id}/download")
async def download_document(
    doc_id: str,
    db: AsyncSession = Depends(get_db),
    audit: AuditContext = Depends(get_audit_context),
):
    doc = await db.get(ClinicalDocument, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    await audit.record("download", "clinical_document", resource_id=doc_id)
    await db.commit()

    return {
        "document_id": doc.id,
        "file_name": doc.file_name,
        "file_path": doc.file_path,
        "mime_type": doc.mime_type,
        "note": "In production, this would return the actual file via S3 presigned URL",
    }
