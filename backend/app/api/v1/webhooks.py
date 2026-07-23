import hashlib
import hmac

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.prior_auth import PriorAuth
from app.agents.orchestrator import Orchestrator

router = APIRouter()


async def verify_webhook_signature(request: Request) -> bytes:
    """
    Verify the HMAC-SHA256 signature of an inbound webhook.

    Expects X-Webhook-Signature: hex(hmac_sha256(webhook_secret, raw_body)).
    Returns the raw body so handlers don't need to read it twice.
    """
    if not settings.webhook_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Webhooks are not configured (WEBHOOK_SECRET unset)",
        )

    signature = request.headers.get("X-Webhook-Signature", "")
    body = await request.body()
    expected = hmac.new(
        settings.webhook_secret.encode(), body, hashlib.sha256
    ).hexdigest()

    if not signature or not hmac.compare_digest(signature, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature",
        )
    return body


@router.post("/covermymeds")
async def covermymeds_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    _body: bytes = Depends(verify_webhook_signature),
):
    """
    Handle CoverMyMeds status update callbacks.
    CoverMyMeds sends webhooks when PA status changes.
    """
    body = await request.json()

    pa_number = body.get("pa_id") or body.get("request_id")
    webhook_status = (body.get("status") or "").lower()

    if not pa_number:
        return {"received": True, "processed": False, "reason": "No PA identifier"}

    stmt = select(PriorAuth).where(PriorAuth.pa_number == pa_number)
    result = await db.execute(stmt)
    pa = result.scalar_one_or_none()

    if not pa:
        return {"received": True, "processed": False, "reason": "PA not found"}

    condition_map = {
        "approved": "approved",
        "denied": "denied",
        "pending": "pending",
        "need_more_info": "pending",
    }
    condition = condition_map.get(webhook_status)
    if condition is None:
        return {"received": True, "processed": False, "reason": f"Unknown status '{webhook_status}'"}

    orchestrator = Orchestrator(db)
    await orchestrator.advance(pa.id, condition=condition)

    return {"received": True, "processed": True, "pa_id": pa.id, "new_condition": condition}


@router.post("/epa")
async def epa_webhook(
    request: Request,
    _body: bytes = Depends(verify_webhook_signature),
):
    """Handle ePA (NCPDP SCRIPT) status callbacks. Not yet implemented."""
    return {
        "received": True,
        "processed": False,
        "note": "ePA webhook processing not implemented",
    }


@router.post("/fax")
async def fax_webhook(
    request: Request,
    _body: bytes = Depends(verify_webhook_signature),
):
    """Handle fax delivery/receipt callbacks. Not yet implemented."""
    body = await request.json()
    return {
        "received": True,
        "processed": False,
        "fax_status": body.get("status"),
        "reference": body.get("reference_id"),
    }
