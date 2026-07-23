from app.celery_app import celery
from app.tasks.worker_db import run_task


@celery.task(name="app.tasks.followup_tasks.process_scheduled_followups")
def process_scheduled_followups():
    """
    Periodic task: Process follow-up escalations.
    Runs every hour via Celery Beat.
    Checks PAs in doctor_outreach or followup_pending status
    and triggers the follow-up agent.
    """
    from app.models.prior_auth import PriorAuth
    from app.agents.orchestrator import Orchestrator
    from sqlalchemy import select

    async def _process(db):
        stmt = select(PriorAuth).where(
            PriorAuth.status.in_(["doctor_outreach", "followup_pending"]),
            PriorAuth.escalated == False,
        )
        result = await db.execute(stmt)
        followup_pas = result.scalars().all()

        orchestrator = Orchestrator(db)
        processed = 0
        for pa in followup_pas:
            await orchestrator.trigger_agent(pa.id, "followup")
            processed += 1

        return processed

    count = run_task(_process)
    return {"processed": count, "task": "process_scheduled_followups"}
