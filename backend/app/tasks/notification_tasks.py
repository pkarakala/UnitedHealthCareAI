from app.celery_app import celery


@celery.task(name="app.tasks.notification_tasks.send_notification")
def send_notification(communication_id: str):
    """
    Async task: Send a single notification (SMS, email, fax).
    Called when communications are queued by agents.
    """
    import asyncio
    from app.database import AsyncSessionLocal
    from app.models.communication import Communication
    from datetime import datetime, timezone

    async def _send():
        async with AsyncSessionLocal() as db:
            comm = await db.get(Communication, communication_id)
            if not comm:
                return {"error": "Communication not found"}

            # In production, dispatch to appropriate service:
            # SMS -> Twilio
            # Email -> SendGrid/SES
            # Fax -> RingCentral/SRFax
            # Portal -> EHR API

            # Simulate sending
            comm.status = "sent"
            comm.sent_at = datetime.now(timezone.utc)
            await db.commit()

            return {"sent": True, "channel": comm.channel, "id": communication_id}

    return asyncio.run(_send())


@celery.task(name="app.tasks.notification_tasks.send_batch_notifications")
def send_batch_notifications(prior_auth_id: str):
    """Send all pending notifications for a PA case."""
    import asyncio
    from app.database import AsyncSessionLocal
    from app.models.communication import Communication
    from sqlalchemy import select
    from datetime import datetime, timezone

    async def _send_batch():
        async with AsyncSessionLocal() as db:
            stmt = select(Communication).where(
                Communication.prior_auth_id == prior_auth_id,
                Communication.status == "pending",
            )
            result = await db.execute(stmt)
            pending = result.scalars().all()

            sent = 0
            for comm in pending:
                comm.status = "sent"
                comm.sent_at = datetime.now(timezone.utc)
                sent += 1

            await db.commit()
            return sent

    count = asyncio.run(_send_batch())
    return {"sent": count, "prior_auth_id": prior_auth_id}
