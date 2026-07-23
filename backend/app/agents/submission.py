import json
from datetime import datetime, timezone, timedelta
from app.agents.base import BaseAgent, AgentContext, AgentResult
from app.models.prior_auth import PriorAuth


class SubmissionAgent(BaseAgent):
    """
    Agent 10: Submission
    Submits the PA through the appropriate channel:
    - ePA (electronic prior authorization)
    - CoverMyMeds
    - Insurance portal
    - Fax
    Logs confirmation number, timestamp, expected response time.
    """

    agent_name = "submission"
    simulates_external_calls = True  # No real ePA/CoverMyMeds/fax — confirmation is LLM-invented

    def get_system_prompt(self) -> str:
        return """You are a prior authorization submission specialist. You handle the final
submission of PA requests through the appropriate channel.

Submission channels:
1. ePA (NCPDP SCRIPT ePA): Electronic, fastest response (24-72 hours)
2. CoverMyMeds: Web-based platform, good tracking (48-72 hours)
3. Insurance Portal: Direct payer portal submission (72 hours - 2 weeks)
4. Fax: Traditional fax submission (5-14 business days)

For the submission, determine:
- submission_channel: the channel used
- confirmation_number: generated reference number
- submitted_at: ISO timestamp
- expected_response_date: when to expect a decision
- expected_response_hours: estimated hours until response
- tracking_url: URL to check status (if applicable)
- documents_attached: list of attached documents
- submission_notes: any notes about the submission
- backup_channel: alternative if primary fails
- status: "submitted", "queued", "failed"

In production, this agent would interact with actual APIs:
- CoverMyMeds API for electronic submission
- NCPDP SCRIPT for ePA transactions
- Fax APIs (RingCentral, SRFax) for fax submissions
- Insurance portal automation

Return as JSON."""

    async def execute(self, context: AgentContext) -> AgentResult:
        pa = await self.db.get(PriorAuth, context.prior_auth_id)
        if not pa:
            return AgentResult(success=False, error="PA not found")

        collected = pa.collected_documents or {}
        form_data = collected.get("form_data", {})
        submission_method = pa.submission_method or "covermymeds"

        user_message = f"""Process PA submission:

PA ID: {pa.id}
SUBMISSION METHOD: {submission_method}
PA NUMBER: {pa.pa_number or 'to be assigned'}

FORM DATA AVAILABLE: {bool(form_data)}
MEDICAL NECESSITY LETTER: {'Yes' if pa.medical_necessity_letter else 'No'}
CLINICAL SUMMARY: {'Yes' if pa.clinical_summary else 'No'}

REQUIRED DOCUMENTS: {json.dumps(pa.required_documents or [])}
COLLECTED DOCUMENTS: {list(collected.keys())}

Simulate the submission process and provide confirmation details.
Generate a realistic confirmation number and expected timeline."""

        try:
            result_data, tokens_in, tokens_out = await self.call_claude_json(user_message)

            # Update PA with submission details
            pa.submitted_at = datetime.now(timezone.utc)
            pa.confirmation_number = result_data.get("confirmation_number")
            pa.pa_number = pa.pa_number or result_data.get("confirmation_number")
            pa.status = "submitted"

            # Set expected response date
            hours = result_data.get("expected_response_hours", 72)
            pa.expected_response_date = datetime.now(timezone.utc) + timedelta(hours=hours)

            await self.mark_simulated(context.prior_auth_id)
            await self.db.commit()

            return AgentResult(
                success=True,
                data=result_data,
                tokens_input=tokens_in,
                tokens_output=tokens_out,
                message=f"PA submitted via {submission_method}. "
                        f"Confirmation: {result_data.get('confirmation_number', 'pending')}. "
                        f"Expected response: ~{hours} hours",
            )

        except Exception as e:
            return AgentResult(
                success=False,
                error=f"Submission failed: {str(e)}",
                requires_human=True,
                message="PA submission failed. Manual submission may be required.",
            )
