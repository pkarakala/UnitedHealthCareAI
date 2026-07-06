from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.agent_execution import AgentExecution
from app.schemas.agent import AgentExecutionRead
from app.utils.constants import AgentType

router = APIRouter()


@router.get("/types")
async def list_agent_types():
    """List all available agent types."""
    return {
        "agents": [
            {"name": agent.value, "description": _get_agent_description(agent.value)}
            for agent in AgentType
        ]
    }


@router.get("/executions", response_model=list[AgentExecutionRead])
async def list_executions(
    skip: int = 0,
    limit: int = 50,
    agent_name: str = None,
    prior_auth_id: str = None,
    status: str = None,
    db: AsyncSession = Depends(get_db),
):
    """List agent execution history."""
    stmt = select(AgentExecution).offset(skip).limit(limit).order_by(
        AgentExecution.started_at.desc()
    )
    if agent_name:
        stmt = stmt.where(AgentExecution.agent_name == agent_name)
    if prior_auth_id:
        stmt = stmt.where(AgentExecution.prior_auth_id == prior_auth_id)
    if status:
        stmt = stmt.where(AgentExecution.status == status)

    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/stats")
async def get_agent_stats(db: AsyncSession = Depends(get_db)):
    """Get aggregate agent statistics."""
    stmt = select(
        AgentExecution.agent_name,
        func.count(AgentExecution.id).label("total_runs"),
        func.avg(AgentExecution.duration_ms).label("avg_duration_ms"),
        func.sum(AgentExecution.tokens_input).label("total_input_tokens"),
        func.sum(AgentExecution.tokens_output).label("total_output_tokens"),
    ).group_by(AgentExecution.agent_name)

    result = await db.execute(stmt)
    rows = result.all()

    return [
        {
            "agent_name": row.agent_name,
            "total_runs": row.total_runs,
            "avg_duration_ms": round(float(row.avg_duration_ms or 0), 1),
            "total_input_tokens": int(row.total_input_tokens or 0),
            "total_output_tokens": int(row.total_output_tokens or 0),
        }
        for row in rows
    ]


def _get_agent_description(name: str) -> str:
    descriptions = {
        "prescription_intake": "Extracts prescription data via OCR/Vision",
        "pa_detection": "Determines if prior authorization is required",
        "insurance_verification": "Verifies patient insurance eligibility",
        "clinical_requirement": "Identifies required clinical documentation",
        "patient_record": "Retrieves patient medical records",
        "doctor_communication": "Generates prescriber outreach messages",
        "followup": "Manages follow-up escalation timeline",
        "pa_form_filling": "Fills PA submission forms",
        "clinical_writing": "Generates medical necessity letters",
        "submission": "Submits PA to payer",
        "status_monitoring": "Monitors PA decision status",
        "approval": "Processes approved PAs",
        "denial_analysis": "Analyzes denial reasons and strategy",
        "appeal": "Drafts appeal letters",
        "patient_communication": "Sends patient notifications",
        "revenue_analytics": "Computes revenue and performance metrics",
    }
    return descriptions.get(name, "")
