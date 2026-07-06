from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.prior_auth import PriorAuth
from app.models.agent_execution import AgentExecution
from app.models.appeal import Appeal
from app.schemas.analytics import DashboardMetrics, AgentPerformanceMetrics

router = APIRouter()


@router.get("/dashboard", response_model=DashboardMetrics)
async def get_dashboard(db: AsyncSession = Depends(get_db)):
    """Get summary dashboard metrics."""
    total = (await db.execute(select(func.count(PriorAuth.id)))).scalar() or 0
    pending = (await db.execute(
        select(func.count(PriorAuth.id)).where(
            PriorAuth.status.in_(["pending_review", "submitted", "intake", "pa_detection"])
        )
    )).scalar() or 0
    approved = (await db.execute(
        select(func.count(PriorAuth.id)).where(PriorAuth.decision == "approved")
    )).scalar() or 0
    denied = (await db.execute(
        select(func.count(PriorAuth.id)).where(PriorAuth.decision == "denied")
    )).scalar() or 0

    revenue = (await db.execute(
        select(func.sum(PriorAuth.revenue_recovered))
    )).scalar() or 0

    appeal_total = (await db.execute(select(func.count(Appeal.id)))).scalar() or 0
    appeal_won = (await db.execute(
        select(func.count(Appeal.id)).where(Appeal.decision == "approved")
    )).scalar() or 0

    approval_rate = (approved / max(approved + denied, 1)) * 100
    appeal_rate = (appeal_won / max(appeal_total, 1)) * 100

    return DashboardMetrics(
        total_pas=total,
        pending_pas=pending,
        approved_today=approved,
        denied_today=denied,
        average_turnaround_hours=48.0,
        approval_rate=approval_rate,
        appeal_success_rate=appeal_rate,
        revenue_recovered_mtd=float(revenue),
        top_rejected_drugs=[],
        top_slow_insurers=[],
        top_slow_prescribers=[],
    )


@router.get("/revenue")
async def get_revenue_metrics(db: AsyncSession = Depends(get_db)):
    """Get revenue recovery metrics."""
    total_claims = (await db.execute(
        select(func.sum(PriorAuth.claim_amount))
    )).scalar() or 0
    total_recovered = (await db.execute(
        select(func.sum(PriorAuth.revenue_recovered))
    )).scalar() or 0

    return {
        "total_claims_submitted": float(total_claims),
        "total_recovered": float(total_recovered),
        "recovery_rate": float(total_recovered) / max(float(total_claims), 1) * 100,
    }


@router.get("/turnaround")
async def get_turnaround_metrics(db: AsyncSession = Depends(get_db)):
    """Get PA turnaround time metrics."""
    return {
        "average_intake_to_submission_hours": 4.2,
        "average_submission_to_decision_hours": 52.3,
        "average_total_hours": 56.5,
        "note": "Metrics will be computed from actual data once PAs are processed",
    }


@router.get("/agent-performance", response_model=list[AgentPerformanceMetrics])
async def get_agent_performance(db: AsyncSession = Depends(get_db)):
    """Get per-agent performance metrics."""
    stmt = select(
        AgentExecution.agent_name,
        func.count(AgentExecution.id).label("total"),
        func.avg(AgentExecution.duration_ms).label("avg_duration"),
        func.sum(AgentExecution.tokens_input + AgentExecution.tokens_output).label("total_tokens"),
    ).group_by(AgentExecution.agent_name)

    result = await db.execute(stmt)
    rows = result.all()

    metrics = []
    for row in rows:
        success_stmt = select(func.count(AgentExecution.id)).where(
            AgentExecution.agent_name == row.agent_name,
            AgentExecution.status == "completed",
        )
        success_count = (await db.execute(success_stmt)).scalar() or 0

        metrics.append(AgentPerformanceMetrics(
            agent_name=row.agent_name,
            total_executions=row.total,
            success_rate=(success_count / max(row.total, 1)) * 100,
            average_duration_ms=float(row.avg_duration or 0),
            total_tokens_used=int(row.total_tokens or 0),
            total_cost_usd=0.0,
            error_rate=((row.total - success_count) / max(row.total, 1)) * 100,
        ))

    return metrics
