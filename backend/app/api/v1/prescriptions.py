import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.prescription import Prescription
from app.schemas.prescription import PrescriptionCreate, PrescriptionRead
from app.agents.orchestrator import Orchestrator

router = APIRouter()


@router.post("/intake", response_model=dict)
async def intake_prescription(
    patient_id: str = Form(...),
    prescriber_npi: str = Form(...),
    drug_name: str = Form(...),
    prescriber_name: str = Form(None),
    prescriber_phone: str = Form(None),
    prescriber_fax: str = Form(None),
    strength: str = Form(None),
    quantity: int = Form(None),
    days_supply: int = Form(None),
    directions: str = Form(None),
    ndc: str = Form(None),
    insurance_id: str = Form(None),
    image: UploadFile = File(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Intake a new prescription. Accepts form data and optional image upload.
    Automatically triggers the PA workflow if PA detection determines it's needed.
    """
    rx_id = str(uuid.uuid4())

    # Save image if uploaded
    image_url = None
    if image:
        image_url = f"uploads/prescriptions/{rx_id}/{image.filename}"

    prescription = Prescription(
        id=rx_id,
        patient_id=patient_id,
        prescriber_npi=prescriber_npi,
        prescriber_name=prescriber_name,
        prescriber_phone=prescriber_phone,
        prescriber_fax=prescriber_fax,
        drug_name=drug_name,
        strength=strength,
        quantity=quantity,
        days_supply=days_supply,
        directions=directions,
        ndc=ndc,
        raw_image_url=image_url,
        source="electronic" if not image else "scan",
        status="intake",
    )
    db.add(prescription)
    await db.commit()

    # Start the PA workflow
    orchestrator = Orchestrator(db)
    pa_id = await orchestrator.start_workflow(
        prescription_id=rx_id,
        patient_id=patient_id,
        insurance_id=insurance_id,
    )

    return {
        "prescription_id": rx_id,
        "prior_auth_id": pa_id,
        "status": "workflow_started",
        "message": f"Prescription intake complete. PA workflow initiated for {drug_name}.",
    }


@router.post("", response_model=PrescriptionRead)
async def create_prescription(
    data: PrescriptionCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a prescription record without triggering the full workflow."""
    prescription = Prescription(
        id=str(uuid.uuid4()),
        **data.model_dump(),
    )
    db.add(prescription)
    await db.commit()
    await db.refresh(prescription)
    return prescription


@router.get("", response_model=list[PrescriptionRead])
async def list_prescriptions(
    skip: int = 0,
    limit: int = 50,
    status: str = None,
    patient_id: str = None,
    db: AsyncSession = Depends(get_db),
):
    """List prescriptions with optional filters."""
    stmt = select(Prescription).offset(skip).limit(limit).order_by(
        Prescription.created_at.desc()
    )
    if status:
        stmt = stmt.where(Prescription.status == status)
    if patient_id:
        stmt = stmt.where(Prescription.patient_id == patient_id)

    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{prescription_id}", response_model=PrescriptionRead)
async def get_prescription(
    prescription_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a single prescription by ID."""
    prescription = await db.get(Prescription, prescription_id)
    if not prescription:
        raise HTTPException(status_code=404, detail="Prescription not found")
    return prescription
