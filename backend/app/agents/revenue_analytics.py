import json
from sqlalchemy import select, func
from app.agents.base import BaseAgent, AgentContext, AgentResult
from app.models.prior_auth import PriorAuth
from app.models.agent_execution import AgentExecution


class RevenueAnalyticsAgent(BaseAgent):
    """
    Agent 16: Revenue Analytics
    Tracks and computes metrics:
    - Average approval time
    - Revenue recovered
    - Top rejected drugs
    - Top slow physicians
    - Top slow insurance companies
    - PA completion rate
    - Technician productivity
    - Money recovered via appeals
    """

    agent_name = "revenue_analytics"

    def get_system_prompt(self) -> str:
        return """You are a pharmacy revenue analytics specialist. You analyze PA workflow
data to generate actionable business intelligence for pharmacy owners.

Key metrics to compute:
1. Average approval turnaround time (by insurance, by drug)
2. Total revenue recovered (approved PAs * claim amounts)
3. Top rejected drugs (which drugs get denied most)
4. Top slow prescribers (who takes longest to respond)
5. Top slow insurance companies (which payers take longest)
6. PA completion rate (started vs completed)
7. Appeal success rate
8. Revenue recovered via appeals
9. Average cost per PA (time + AI tokens)
10. Technician productivity (PAs handled per day)

For the analytics report, provide:
- period: time period analyzed
- summary_metrics: key numbers
- approval_rate: percentage
- average_turnaround_hours: mean time to decision
- revenue_recovered: total dollars recovered
- top_rejected_drugs: list with counts
- top_slow_prescribers: list with avg response times
- top_slow_insurers: list with avg decision times
- appeal_metrics: appeal success rate and recovered revenue
- trends: week-over-week or month-over-month changes
- recommendations: actionable insights for the pharmacy
- cost_savings: estimated labor savings from automation

Return as JSON."""

    async def execute(self, context: AgentContext) -> AgentResult:
        # Query aggregate data from the database
        pa = await self.db.get(PriorAuth, context.prior_auth_id)

        # Get overall PA statistics
        total_stmt = select(func.count(PriorAuth.id))
        total_result = await self.db.execute(total_stmt)
        total_pas = total_result.scalar() or 0

        approved_stmt = select(func.count(PriorAuth.id)).where(
            PriorAuth.status.in_(["approved", "completed"])
        )
        approved_result = await self.db.execute(approved_stmt)
        approved_count = approved_result.scalar() or 0

        denied_stmt = select(func.count(PriorAuth.id)).where(
            PriorAuth.status.in_(["denied", "appeal_denied"])
        )
        denied_result = await self.db.execute(denied_stmt)
        denied_count = denied_result.scalar() or 0

        # Revenue data
        revenue_stmt = select(func.sum(PriorAuth.revenue_recovered))
        revenue_result = await self.db.execute(revenue_stmt)
        total_revenue = revenue_result.scalar() or 0

        user_message = f"""Generate analytics report for this PA and overall pharmacy metrics:

CURRENT PA:
- Drug: {pa.prescription_id if pa else 'N/A'}
- Status: {pa.status if pa else 'N/A'}
- Revenue: ${pa.revenue_recovered or 0 if pa else 0}

AGGREGATE METRICS:
- Total PAs in system: {total_pas}
- Approved: {approved_count}
- Denied: {denied_count}
- Total Revenue Recovered: ${total_revenue}
- Approval Rate: {(approved_count/max(total_pas,1))*100:.1f}%

Generate a comprehensive analytics report with insights and recommendations.
Include cost savings estimates from AI automation vs manual processing."""

        try:
            result_data, tokens_in, tokens_out = await self.call_claude_json(user_message)

            return AgentResult(
                success=True,
                data=result_data,
                tokens_input=tokens_in,
                tokens_output=tokens_out,
                message=f"Analytics computed. Approval rate: {result_data.get('approval_rate', 'N/A')}%. "
                        f"Revenue recovered: ${result_data.get('revenue_recovered', 0)}",
            )

        except Exception as e:
            return AgentResult(
                success=False,
                error=f"Analytics computation failed: {str(e)}",
            )
