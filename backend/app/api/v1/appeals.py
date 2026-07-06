import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.appeal import Appeal
from app.models.prior_auth import PriorAuth
from app.schemas.appeal import AppealCreate, AppealRead
from app.agents.orchestrator import Orchestrator

router = APIRouter()


@router.post("", response_model=AppealRead)
async def create_appeal(data: AppealCreate, db: AsyncSession = Depends(get_db)):
    """Initiate an appeal for a denied PA."""
    pa = await db.get(PriorAuth, data.prior_auth_id)
    if not pa:
        raise HTTPException(status_code=404, detail="Prior authorization not found")

    appeal = Appeal(id=str(uuid.uuid4()), **data.model_dump())
    db.add(appeal)
    await db.commit()
    await db.refresh(appeal)

    # Trigger appeal agent
    orchestrator = Orchestrator(db)
    await orchestrator.trigger_agent(data.prior_auth_id, "appeal")

    return appeal


@router.get("", response_model=list[AppealRead])
async def list_appeals(
    skip: int = 0,
    limit: int = 50,
    prior_auth_id: str = None,
    status: str = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Appeal).offset(skip).limit(limit).order_by(Appeal.created_at.desc())
    if prior_auth_id:
        stmt = stmt.where(Appeal.prior_auth_id == prior_auth_id)
    if status:
        stmt = stmt.where(Appeal.status == status)

    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{appeal_id}", response_model=AppealRead)
async def get_appeal(appeal_id: str, db: AsyncSession = Depends(get_db)):
    appeal = await db.get(Appeal, appeal_id)
    if not appeal:
        raise HTTPException(status_code=404, detail="Appeal not found")
    return appeal


@router.put("/{appeal_id}", response_model=AppealRead)
async def update_appeal(
    appeal_id: str,
    status: str = None,
    decision: str = None,
    db: AsyncSession = Depends(get_db),
):
    appeal = await db.get(Appeal, appeal_id)
    if not appeal:
        raise HTTPException(status_code=404, detail="Appeal not found")

    if status:
        appeal.status = status
    if decision:
        appeal.decision = decision

    await db.commit()
    await db.refresh(appeal)
    return appeal
