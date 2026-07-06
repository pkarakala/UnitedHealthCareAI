from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.prior_auth import PriorAuth
from app.models.agent_execution import AgentExecution
from app.utils.constants import PAStatus


class PAService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_pa_with_history(self, pa_id: str) -> dict:
        pa = await self.db.get(PriorAuth, pa_id)
        if not pa:
            return None

        stmt = select(AgentExecution).where(
            AgentExecution.prior_auth_id == pa_id
        ).order_by(AgentExecution.started_at)
        result = await self.db.execute(stmt)
        executions = result.scalars().all()

        return {
            "prior_auth": pa,
            "executions": executions,
            "total_tokens": sum(
                (e.tokens_input or 0) + (e.tokens_output or 0) for e in executions
            ),
            "total_duration_ms": sum(e.duration_ms or 0 for e in executions),
        }

    async def get_active_pas(self) -> list[PriorAuth]:
        terminal_states = [
            PAStatus.COMPLETED.value,
            PAStatus.CANCELLED.value,
            PAStatus.NO_PA_REQUIRED.value,
        ]
        stmt = select(PriorAuth).where(
            PriorAuth.status.not_in(terminal_states)
        ).order_by(PriorAuth.priority, PriorAuth.created_at)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_stats(self) -> dict:
        total = (await self.db.execute(select(func.count(PriorAuth.id)))).scalar() or 0
        active = len(await self.get_active_pas())
        approved = (await self.db.execute(
            select(func.count(PriorAuth.id)).where(PriorAuth.decision == "approved")
        )).scalar() or 0

        return {
            "total": total,
            "active": active,
            "approved": approved,
            "approval_rate": (approved / max(total, 1)) * 100,
        }
