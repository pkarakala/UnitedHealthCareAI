from app.celery_app import celery


@celery.task(name="app.tasks.followup_tasks.process_scheduled_followups")
def process_scheduled_followups():
    """
    Periodic task: Process follow-up escalations.
    Runs every hour via Celery Beat.
    Checks PAs in doctor_outreach or followup_pending status
    and triggers the follow-up agent.
    """
    import asyncio
    from app.database import AsyncSessionLocal
    from app.models.prior_auth import PriorAuth
    from app.agents.orchestrator import Orchestrator
    from sqlalchemy import select

    async def _process():
        async with AsyncSessionLocal() as db:
            stmt = select(PriorAuth).where(
                PriorAuth.status.in_(["doctor_outreach", "followup_pending"]),
                PriorAuth.escalated == False,
            )
            result = await db.execute(stmt)
            followup_pas = result.scalars().all()

            processed = 0
            for pa in followup_pas:
                orchestrator = Orchestrator(db)
                await orchestrator.trigger_agent(pa.id, "followup")
                processed += 1

            return processed

    count = asyncio.run(_process())
    return {"processed": count, "task": "process_scheduled_followups"}
