import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.prior_auth import PriorAuth
from app.models.patient import Patient
from app.models.prescription import Prescription
from app.models.agent_execution import AgentExecution
from app.schemas.prior_auth import (
    PriorAuthCreate,
    PriorAuthRead,
    PriorAuthUpdate,
    PriorAuthTimeline,
    TimelineEvent,
)
from app.schemas.agent import AgentTriggerRequest
from app.agents.orchestrator import Orchestrator
from app.services.audit_service import AuditContext, get_audit_context

router = APIRouter()


@router.post("", response_model=PriorAuthRead)
async def create_prior_auth(
    data: PriorAuthCreate,
    db: AsyncSession = Depends(get_db),
):
    """Manually create a PA case."""
    pa = PriorAuth(id=str(uuid.uuid4()), **data.model_dump())
    db.add(pa)
    await db.commit()
    await db.refresh(pa)
    return pa


@router.get("", response_model=list[PriorAuthRead])
async def list_prior_auths(
    skip: int = 0,
    limit: int = 50,
    status: str = None,
    patient_id: str = None,
    escalated: bool = None,
    db: AsyncSession = Depends(get_db),
):
    """List PA cases with filters, joined with patient + drug display fields."""
    stmt = (
        select(PriorAuth, Patient, Prescription.drug_name)
        .join(Patient, PriorAuth.patient_id == Patient.id)
        .join(Prescription, PriorAuth.prescription_id == Prescription.id)
        .offset(skip)
        .limit(limit)
        .order_by(PriorAuth.created_at.desc())
    )
    if status:
        stmt = stmt.where(PriorAuth.status == status)
    if patient_id:
        stmt = stmt.where(PriorAuth.patient_id == patient_id)
    if escalated is not None:
        stmt = stmt.where(PriorAuth.escalated == escalated)

    rows = (await db.execute(stmt)).all()
    results = []
    for pa, patient, drug_name in rows:
        item = PriorAuthRead.model_validate(pa)
        item.patient_name = f"{patient.last_name}, {patient.first_name}"
        item.patient_dob = str(patient.date_of_birth)
        item.drug_name = drug_name
        results.append(item)
    return results


@router.get("/{pa_id}", response_model=PriorAuthRead)
async def get_prior_auth(
    pa_id: str,
    db: AsyncSession = Depends(get_db),
    audit: AuditContext = Depends(get_audit_context),
):
    """Get a single PA case."""
    pa = await db.get(PriorAuth, pa_id)
    if not pa:
        raise HTTPException(status_code=404, detail="Prior authorization not found")
    await audit.record("read", "prior_auth", resource_id=pa_id)
    await db.commit()
    return pa


@router.put("/{pa_id}", response_model=PriorAuthRead)
async def update_prior_auth(
    pa_id: str,
    data: PriorAuthUpdate,
    db: AsyncSession = Depends(get_db),
    audit: AuditContext = Depends(get_audit_context),
):
    """Update a PA case."""
    pa = await db.get(PriorAuth, pa_id)
    if not pa:
        raise HTTPException(status_code=404, detail="Prior authorization not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(pa, field, value)

    await audit.record(
        "update", "prior_auth", resource_id=pa_id,
        details={"fields": list(update_data.keys())},
    )
    await db.commit()
    await db.refresh(pa)
    return pa


@router.get("/{pa_id}/timeline", response_model=PriorAuthTimeline)
async def get_pa_timeline(
    pa_id: str,
    db: AsyncSession = Depends(get_db),
    audit: AuditContext = Depends(get_audit_context),
):
    """Get the execution timeline for a PA case."""
    pa = await db.get(PriorAuth, pa_id)
    if not pa:
        raise HTTPException(status_code=404, detail="Prior authorization not found")
    await audit.record("read", "prior_auth_timeline", resource_id=pa_id)
    await db.commit()

    stmt = select(AgentExecution).where(
        AgentExecution.prior_auth_id == pa_id
    ).order_by(AgentExecution.started_at)
    result = await db.execute(stmt)
    executions = result.scalars().all()

    events = [
        TimelineEvent(
            timestamp=ex.started_at,
            agent_name=ex.agent_name,
            action=f"{ex.agent_name} execution",
            status=ex.status,
            details=ex.output_data,
            duration_ms=ex.duration_ms,
        )
        for ex in executions
    ]

    total_hours = None
    if executions and len(executions) > 1:
        first = executions[0].started_at
        last = executions[-1].completed_at or executions[-1].started_at
        total_hours = (last - first).total_seconds() / 3600

    return PriorAuthTimeline(
        prior_auth_id=pa_id,
        current_status=pa.status,
        events=events,
        total_duration_hours=total_hours,
    )


@router.post("/{pa_id}/trigger/{agent_name}")
async def trigger_agent(
    pa_id: str,
    agent_name: str,
    force: bool = Query(False),
    db: AsyncSession = Depends(get_db),
):
    """Manually trigger a specific agent on a PA case."""
    pa = await db.get(PriorAuth, pa_id)
    if not pa:
        raise HTTPException(status_code=404, detail="Prior authorization not found")

    orchestrator = Orchestrator(db)
    result = await orchestrator.trigger_agent(pa_id, agent_name, force=force)

    return {
        "success": result.success,
        "agent": agent_name,
        "message": result.message,
        "data": result.data,
        "requires_human": result.requires_human,
    }


@router.post("/{pa_id}/advance")
async def advance_workflow(
    pa_id: str,
    condition: str = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Manually advance the PA workflow with an optional condition."""
    pa = await db.get(PriorAuth, pa_id)
    if not pa:
        raise HTTPException(status_code=404, detail="Prior authorization not found")

    orchestrator = Orchestrator(db)
    result = await orchestrator.advance(pa_id, condition=condition)

    if not result:
        return {"message": "No valid transition from current state", "status": pa.status}

    return {
        "success": result.success,
        "message": result.message,
        "new_status": pa.status,
    }


@router.post("/{pa_id}/cancel")
async def cancel_prior_auth(
    pa_id: str,
    db: AsyncSession = Depends(get_db),
    audit: AuditContext = Depends(get_audit_context),
):
    """Cancel a PA case."""
    pa = await db.get(PriorAuth, pa_id)
    if not pa:
        raise HTTPException(status_code=404, detail="Prior authorization not found")

    pa.status = "cancelled"
    pa.current_agent = None
    await audit.record("cancel", "prior_auth", resource_id=pa_id, phi_accessed=False)
    await db.commit()

    return {"message": "Prior authorization cancelled", "id": pa_id}


@router.post("/{pa_id}/escalate")
async def escalate_prior_auth(
    pa_id: str,
    assigned_to: str = Query(None),
    db: AsyncSession = Depends(get_db),
    audit: AuditContext = Depends(get_audit_context),
):
    """Escalate a PA case to human review."""
    pa = await db.get(PriorAuth, pa_id)
    if not pa:
        raise HTTPException(status_code=404, detail="Prior authorization not found")

    pa.escalated = True
    pa.sub_status = "escalated_to_human"
    if assigned_to:
        pa.assigned_to = assigned_to
    await audit.record(
        "escalate", "prior_auth", resource_id=pa_id,
        details={"assigned_to": assigned_to}, phi_accessed=False,
    )
    await db.commit()

    return {"message": "Prior authorization escalated", "id": pa_id, "assigned_to": assigned_to}
