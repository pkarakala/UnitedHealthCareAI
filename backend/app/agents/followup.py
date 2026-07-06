import json
from datetime import datetime, timezone, timedelta
from app.agents.base import BaseAgent, AgentContext, AgentResult
from app.models.prior_auth import PriorAuth
from app.models.communication import Communication
from sqlalchemy import select


class FollowupAgent(BaseAgent):
    """
    Agent 7: Follow-up
    Manages escalation timeline when prescriber hasn't responded.
    Day 1: Send reminder
    Day 2: Call office
    Day 4: Portal reminder
    Day 6: Escalate to supervisor/patient
    No human needed unless necessary.
    """

    agent_name = "followup"

    def get_system_prompt(self) -> str:
        return """You are a follow-up and escalation management specialist. You track
prescriber response timelines and generate appropriate follow-up actions.

Escalation Schedule:
- Day 1: Gentle reminder via same channel as initial outreach
- Day 2: Phone call to prescriber's office (generate script)
- Day 4: Multi-channel reminder (fax + portal + phone)
- Day 6: Escalate - notify pharmacy manager, consider contacting patient

For each follow-up action, determine:
- action_type: "reminder", "phone_call", "multi_channel", "escalate"
- channel: communication channel to use
- message: the follow-up message content
- urgency: updated urgency level
- escalation_level: 1-4
- days_since_initial: days since first outreach
- next_followup_date: when to follow up next if no response
- should_escalate_to_human: boolean - whether pharmacy staff should intervene

Return as JSON with:
- current_escalation_level: int
- action: the follow-up action to take
- communications: array of messages to send
- next_check_date: ISO datetime for next check
- should_close: boolean - whether to give up (max attempts reached)
"""

    async def execute(self, context: AgentContext) -> AgentResult:
        pa = await self.db.get(PriorAuth, context.prior_auth_id)
        if not pa:
            return AgentResult(success=False, error="PA not found")

        # Get communication history for this PA
        stmt = select(Communication).where(
            Communication.prior_auth_id == context.prior_auth_id
        ).order_by(Communication.created_at)
        result = await self.db.execute(stmt)
        communications = result.scalars().all()

        # Calculate days since first outreach
        first_outreach = None
        for comm in communications:
            if comm.direction == "outbound":
                first_outreach = comm.created_at
                break

        days_elapsed = 0
        if first_outreach:
            days_elapsed = (datetime.now(timezone.utc) - first_outreach).days

        comm_history = [
            {
                "channel": c.channel,
                "status": c.status,
                "sent_at": str(c.sent_at) if c.sent_at else None,
                "direction": c.direction,
            }
            for c in communications
        ]

        user_message = f"""Determine the appropriate follow-up action:

PA STATUS: {pa.status}
SUB-STATUS: {pa.sub_status}
DAYS SINCE FIRST OUTREACH: {days_elapsed}
RETRY COUNT: {pa.retry_count}

COMMUNICATION HISTORY:
{json.dumps(comm_history, indent=2)}

Based on the escalation schedule and communication history,
determine what follow-up action to take next."""

        try:
            result_data, tokens_in, tokens_out = await self.call_claude_json(user_message)

            # Create follow-up communications
            followup_comms = result_data.get("communications", [])
            for comm_data in followup_comms:
                comm = Communication(
                    prior_auth_id=context.prior_auth_id,
                    channel=comm_data.get("channel", "phone"),
                    direction="outbound",
                    recipient="Prescriber Office",
                    subject=comm_data.get("subject", "Follow-up: PA Documentation"),
                    body=comm_data.get("message", ""),
                    status="pending",
                )
                self.db.add(comm)

            # Update PA
            pa.retry_count += 1
            should_escalate = result_data.get("should_escalate_to_human", False)
            if should_escalate:
                pa.escalated = True
                pa.sub_status = "escalated_to_staff"

            await self.db.commit()

            # Determine next action
            if result_data.get("should_close", False):
                condition = "escalate"
            elif should_escalate:
                condition = "escalate"
            else:
                condition = "awaiting_response"

            return AgentResult(
                success=True,
                data=result_data,
                condition=condition,
                requires_human=should_escalate,
                tokens_input=tokens_in,
                tokens_output=tokens_out,
                message=f"Follow-up level {result_data.get('current_escalation_level', pa.retry_count)}. "
                        f"Action: {result_data.get('action', {}).get('action_type', 'reminder')}",
            )

        except Exception as e:
            return AgentResult(
                success=False,
                error=f"Follow-up processing failed: {str(e)}",
            )
