import json
from datetime import datetime, timezone
from app.agents.base import BaseAgent, AgentContext, AgentResult
from app.models.prior_auth import PriorAuth


class StatusMonitoringAgent(BaseAgent):
    """
    Agent 11: Status Monitoring
    Periodically checks PA status across portals.
    Runs every few hours instead of staff logging into multiple portals.
    Checks: Pending, Approved, Need More Info, Denied, Expired.
    """

    agent_name = "status_monitoring"

    def get_system_prompt(self) -> str:
        return """You are a prior authorization status monitoring specialist. You check
the status of submitted PAs and interpret the results.

Status possibilities:
- pending: Still under review, no action needed
- approved: PA approved, ready to fill
- denied: PA denied, need to analyze reason and consider appeal
- need_more_info: Payer needs additional documentation
- expired: PA expired before decision, may need resubmission
- partial_approval: Approved with modifications (different quantity, duration, etc.)

For each status check, determine:
- current_status: the PA status
- status_changed: boolean - whether status changed since last check
- decision_details: details about the decision if made
- action_required: what needs to happen next
- urgency: "none", "low", "medium", "high"
- next_check_recommended: ISO datetime for next check
- additional_info_requested: list of additional docs if "need_more_info"
- approval_details: if approved - duration, quantity approved, restrictions
- denial_details: if denied - reason code, category, appeal deadline

In production, this would query:
- CoverMyMeds API for ePA status
- Insurance portal scraping/API
- Fax confirmation tracking
- NCPDP response messages

Return as JSON."""

    async def execute(self, context: AgentContext) -> AgentResult:
        pa = await self.db.get(PriorAuth, context.prior_auth_id)
        if not pa:
            return AgentResult(success=False, error="PA not found")

        user_message = f"""Check the status of this PA submission:

PA ID: {pa.id}
PA NUMBER: {pa.pa_number}
CONFIRMATION: {pa.confirmation_number}
SUBMISSION METHOD: {pa.submission_method}
SUBMITTED AT: {pa.submitted_at}
EXPECTED RESPONSE: {pa.expected_response_date}
CURRENT STATUS: {pa.status}
DAYS SINCE SUBMISSION: {(datetime.now(timezone.utc) - pa.submitted_at).days if pa.submitted_at else 0}

Simulate a status check. Based on typical PA timelines and the submission
channel, determine the most likely current status.

Note: In production this would make actual API calls to check real status."""

        try:
            result_data, tokens_in, tokens_out = await self.call_claude_json(user_message)

            current_status = result_data.get("current_status", "pending")

            # Map status to workflow condition
            condition_map = {
                "approved": "approved",
                "denied": "denied",
                "pending": "pending",
                "need_more_info": "pending",
                "expired": "denied",
                "partial_approval": "approved",
            }
            condition = condition_map.get(current_status, "pending")

            # Update PA if decision made
            if current_status in ("approved", "partial_approval"):
                pa.decision = "approved"
                pa.decision_at = datetime.now(timezone.utc)
            elif current_status == "denied":
                pa.decision = "denied"
                pa.decision_at = datetime.now(timezone.utc)
                pa.denial_reason = result_data.get("denial_details", {}).get("reason", "")

            await self.db.commit()

            return AgentResult(
                success=True,
                data=result_data,
                condition=condition,
                tokens_input=tokens_in,
                tokens_output=tokens_out,
                message=f"Status check: {current_status}. "
                        f"{'Decision made!' if current_status != 'pending' else 'Still pending.'}",
            )

        except Exception as e:
            return AgentResult(
                success=False,
                error=f"Status monitoring failed: {str(e)}",
                condition="pending",
            )
