from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.prior_auth import PriorAuth
from app.agents.orchestrator import Orchestrator

router = APIRouter()


@router.post("/covermymeds")
async def covermymeds_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Handle CoverMyMeds status update callbacks.
    CoverMyMeds sends webhooks when PA status changes.
    """
    body = await request.json()

    pa_number = body.get("pa_id") or body.get("request_id")
    status = body.get("status", "").lower()
    decision = body.get("decision")

    if not pa_number:
        return {"received": True, "processed": False, "reason": "No PA identifier"}

    # Find the PA by number
    from sqlalchemy import select
    stmt = select(PriorAuth).where(PriorAuth.pa_number == pa_number)
    result = await db.execute(stmt)
    pa = result.scalar_one_or_none()

    if not pa:
        return {"received": True, "processed": False, "reason": "PA not found"}

    # Map CoverMyMeds status to our conditions
    condition_map = {
        "approved": "approved",
        "denied": "denied",
        "pending": "pending",
        "need_more_info": "pending",
    }
    condition = condition_map.get(status, "pending")

    orchestrator = Orchestrator(db)
    await orchestrator.advance(pa.id, condition=condition)

    return {"received": True, "processed": True, "pa_id": pa.id, "new_condition": condition}


@router.post("/epa")
async def epa_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Handle ePA (NCPDP SCRIPT) status callbacks."""
    body = await request.json()

    return {
        "received": True,
        "processed": True,
        "note": "ePA webhook processing - integrate with NCPDP SCRIPT handler",
    }


@router.post("/fax")
async def fax_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Handle fax delivery/receipt callbacks."""
    body = await request.json()

    fax_status = body.get("status")
    reference_id = body.get("reference_id")

    return {
        "received": True,
        "fax_status": fax_status,
        "reference": reference_id,
    }
