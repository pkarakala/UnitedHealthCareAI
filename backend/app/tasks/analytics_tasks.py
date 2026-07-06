from app.celery_app import celery


@celery.task(name="app.tasks.analytics_tasks.compute_daily_metrics")
def compute_daily_metrics():
    """
    Nightly task: Compute and store daily analytics.
    Runs at 2 AM UTC via Celery Beat.
    Aggregates PA data for the dashboard.
    """
    import asyncio
    from app.database import AsyncSessionLocal
    from app.models.prior_auth import PriorAuth
    from app.models.agent_execution import AgentExecution
    from sqlalchemy import select, func

    async def _compute():
        async with AsyncSessionLocal() as db:
            # Total PAs
            total = (await db.execute(select(func.count(PriorAuth.id)))).scalar() or 0

            # Approval rate
            approved = (await db.execute(
                select(func.count(PriorAuth.id)).where(PriorAuth.decision == "approved")
            )).scalar() or 0
            denied = (await db.execute(
                select(func.count(PriorAuth.id)).where(PriorAuth.decision == "denied")
            )).scalar() or 0

            # Revenue
            revenue = (await db.execute(
                select(func.sum(PriorAuth.revenue_recovered))
            )).scalar() or 0

            # Agent performance
            avg_duration = (await db.execute(
                select(func.avg(AgentExecution.duration_ms))
            )).scalar() or 0

            return {
                "total_pas": total,
                "approved": approved,
                "denied": denied,
                "approval_rate": (approved / max(approved + denied, 1)) * 100,
                "revenue_recovered": float(revenue),
                "avg_agent_duration_ms": float(avg_duration),
            }

    metrics = asyncio.run(_compute())
    return {"metrics": metrics, "task": "compute_daily_metrics"}
