from app.celery_app import celery


@celery.task(name="app.tasks.monitoring_tasks.check_pending_authorizations")
def check_pending_authorizations():
    """
    Periodic task: Check status of all submitted PAs.
    Runs every 2 hours via Celery Beat.
    Queries each pending PA and triggers the status monitoring agent.
    """
    import asyncio
    from app.database import AsyncSessionLocal
    from app.models.prior_auth import PriorAuth
    from app.agents.orchestrator import Orchestrator
    from app.agents.base import AgentContext
    from sqlalchemy import select

    async def _check():
        async with AsyncSessionLocal() as db:
            stmt = select(PriorAuth).where(
                PriorAuth.status.in_(["submitted", "pending_review"])
            )
            result = await db.execute(stmt)
            pending_pas = result.scalars().all()

            for pa in pending_pas:
                orchestrator = Orchestrator(db)
                await orchestrator.trigger_agent(pa.id, "status_monitoring")

            return len(pending_pas)

    count = asyncio.run(_check())
    return {"checked": count, "task": "check_pending_authorizations"}
