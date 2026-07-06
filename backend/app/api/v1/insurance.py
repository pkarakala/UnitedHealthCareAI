import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.insurance import Insurance
from app.schemas.insurance import InsuranceCreate, InsuranceRead, InsuranceVerificationRequest, InsuranceVerificationResult

router = APIRouter()


@router.post("/verify", response_model=InsuranceVerificationResult)
async def verify_insurance(
    data: InsuranceVerificationRequest,
    db: AsyncSession = Depends(get_db),
):
    """Run insurance verification for a member."""
    # In production, this would call real eligibility APIs (Change Healthcare, etc.)
    # For now, return simulated verification
    return InsuranceVerificationResult(
        is_active=True,
        plan_name="Simulated Plan",
        coverage_type="commercial",
        copay=35.0,
        deductible_remaining=500.0,
        step_therapy_required=False,
        quantity_limit_applies=False,
        notes="Simulated verification - integrate with eligibility API for production",
    )


@router.get("/plans", response_model=list[InsuranceRead])
async def list_insurance_plans(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Insurance).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/plans", response_model=InsuranceRead)
async def create_insurance_plan(
    data: InsuranceCreate,
    db: AsyncSession = Depends(get_db),
):
    plan = Insurance(id=str(uuid.uuid4()), **data.model_dump())
    db.add(plan)
    await db.commit()
    await db.refresh(plan)
    return plan


@router.get("/plans/{plan_id}", response_model=InsuranceRead)
async def get_insurance_plan(plan_id: str, db: AsyncSession = Depends(get_db)):
    plan = await db.get(Insurance, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Insurance plan not found")
    return plan
