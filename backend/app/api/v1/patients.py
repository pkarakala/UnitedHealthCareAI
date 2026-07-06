import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.patient import Patient
from app.models.prior_auth import PriorAuth
from app.schemas.patient import PatientCreate, PatientRead, PatientUpdate
from app.schemas.prior_auth import PriorAuthRead

router = APIRouter()


@router.post("", response_model=PatientRead)
async def create_patient(data: PatientCreate, db: AsyncSession = Depends(get_db)):
    patient = Patient(id=str(uuid.uuid4()), **data.model_dump())
    db.add(patient)
    await db.commit()
    await db.refresh(patient)
    return patient


@router.get("", response_model=list[PatientRead])
async def list_patients(
    skip: int = 0,
    limit: int = 50,
    search: str = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Patient).offset(skip).limit(limit).order_by(Patient.created_at.desc())
    if search:
        stmt = stmt.where(
            (Patient.first_name.ilike(f"%{search}%"))
            | (Patient.last_name.ilike(f"%{search}%"))
            | (Patient.member_id.ilike(f"%{search}%"))
        )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{patient_id}", response_model=PatientRead)
async def get_patient(patient_id: str, db: AsyncSession = Depends(get_db)):
    patient = await db.get(Patient, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


@router.put("/{patient_id}", response_model=PatientRead)
async def update_patient(
    patient_id: str,
    data: PatientUpdate,
    db: AsyncSession = Depends(get_db),
):
    patient = await db.get(Patient, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(patient, field, value)

    await db.commit()
    await db.refresh(patient)
    return patient


@router.get("/{patient_id}/prior-auths", response_model=list[PriorAuthRead])
async def get_patient_prior_auths(
    patient_id: str,
    db: AsyncSession = Depends(get_db),
):
    patient = await db.get(Patient, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    stmt = select(PriorAuth).where(
        PriorAuth.patient_id == patient_id
    ).order_by(PriorAuth.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()
