from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.communication import Communication
from app.schemas.communication import CommunicationRead

router = APIRouter()


@router.get("", response_model=list[CommunicationRead])
async def list_communications(
    skip: int = 0,
    limit: int = 50,
    prior_auth_id: str = None,
    channel: str = None,
    status: str = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Communication).offset(skip).limit(limit).order_by(
        Communication.created_at.desc()
    )
    if prior_auth_id:
        stmt = stmt.where(Communication.prior_auth_id == prior_auth_id)
    if channel:
        stmt = stmt.where(Communication.channel == channel)
    if status:
        stmt = stmt.where(Communication.status == status)

    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{comm_id}", response_model=CommunicationRead)
async def get_communication(comm_id: str, db: AsyncSession = Depends(get_db)):
    comm = await db.get(Communication, comm_id)
    if not comm:
        raise HTTPException(status_code=404, detail="Communication not found")
    return comm


@router.post("/{comm_id}/resend")
async def resend_communication(comm_id: str, db: AsyncSession = Depends(get_db)):
    """Resend a failed communication."""
    comm = await db.get(Communication, comm_id)
    if not comm:
        raise HTTPException(status_code=404, detail="Communication not found")

    comm.status = "pending"
    comm.error_message = None
    await db.commit()

    return {"message": "Communication queued for resend", "id": comm_id}
