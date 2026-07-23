from app.celery_app import celery
from app.tasks.worker_db import run_task


@celery.task(name="app.tasks.monitoring_tasks.check_pending_authorizations")
def check_pending_authorizations():
    """
    Periodic task: Check status of all submitted PAs.
    Runs every 2 hours via Celery Beat.
    Queries each pending PA and triggers the status monitoring agent.
    """
    from app.models.prior_auth import PriorAuth
    from app.agents.orchestrator import Orchestrator
    from sqlalchemy import select

    async def _check(db):
        stmt = select(PriorAuth).where(
            PriorAuth.status.in_(["submitted", "pending_review"])
        )
        result = await db.execute(stmt)
        pending_pas = result.scalars().all()

        orchestrator = Orchestrator(db)
        for pa in pending_pas:
            await orchestrator.trigger_agent(pa.id, "status_monitoring")

        return len(pending_pas)

    count = run_task(_check)
    return {"checked": count, "task": "check_pending_authorizations"}
