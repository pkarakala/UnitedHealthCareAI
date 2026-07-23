import json
import re
from datetime import datetime, timezone
from app.agents.base import BaseAgent, AgentContext, AgentResult
from app.models.prior_auth import PriorAuth
from app.models.prescription import Prescription
from app.models.communication import Communication


def _coerce_money(value) -> float:
    """Best-effort parse of an LLM-provided monetary value into a float."""
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = re.sub(r"[^0-9.\-]", "", value)
        try:
            return float(cleaned) if cleaned not in ("", "-", ".", "-.") else 0.0
        except ValueError:
            return 0.0
    return 0.0


class ApprovalAgent(BaseAgent):
    """
    Agent 12: Approval Processing
    When PA is approved, automatically:
    - Updates pharmacy software status
    - Prepares claim reversal and rebill
    - Generates fill instructions
    - Notifies technician
    - Notifies patient
    """

    agent_name = "approval"

    def get_system_prompt(self) -> str:
        return """You are a pharmacy PA approval processing specialist. When a PA is approved,
you coordinate all downstream actions to ensure the prescription gets filled.

Approval processing steps:
1. Update pharmacy management system with approval details
2. Reverse any rejected claim
3. Prepare rebill with PA override code
4. Generate label/fill instructions for technicians
5. Calculate copay/patient responsibility
6. Prepare patient notification
7. Set PA expiration tracking

Generate an approval processing plan:
- system_updates: list of system records to update
- claim_action: "reverse_and_rebill", "new_claim", "none"
- override_codes: PA override codes for claim
- pa_authorization_number: the auth number to use
- pa_valid_from: start date of authorization
- pa_valid_to: expiration date
- quantity_authorized: approved quantity
- fills_authorized: number of fills approved
- technician_instructions: what the tech needs to do
- patient_copay_estimate: estimated patient cost
- patient_notification: message for the patient
- follow_up_actions: any additional steps needed
- revenue_impact: estimated revenue from this approval

Return as JSON."""

    async def execute(self, context: AgentContext) -> AgentResult:
        pa = await self.db.get(PriorAuth, context.prior_auth_id)
        prescription = await self.db.get(Prescription, context.prescription_id)

        if not pa or not prescription:
            return AgentResult(success=False, error="PA or prescription not found")

        user_message = f"""Process this PA approval:

PA NUMBER: {pa.pa_number}
DRUG: {prescription.drug_name} {prescription.strength or ''}
QUANTITY: {prescription.quantity}
DAYS SUPPLY: {prescription.days_supply}
DECISION: {pa.decision}
DECISION DATE: {pa.decision_at}
CLAIM AMOUNT: ${pa.claim_amount or 'TBD'}
SUBMISSION METHOD: {pa.submission_method}

Generate the complete approval processing plan including system updates,
claim handling, technician instructions, and patient notification."""

        try:
            result_data, tokens_in, tokens_out = await self.call_claude_json(user_message)

            # Update PA with revenue data. Claude may return a non-numeric
            # string (e.g. "TBD", "$1,200"), so coerce defensively.
            pa.revenue_recovered = _coerce_money(result_data.get("revenue_impact"))

            pa.status = "approved"
            pa.sub_status = "ready_to_fill"

            # Create patient notification
            patient_msg = result_data.get("patient_notification", "Your prescription has been approved.")
            comm = Communication(
                prior_auth_id=context.prior_auth_id,
                channel="sms",
                direction="outbound",
                recipient="patient",
                subject="PA Approved",
                body=patient_msg,
                status="pending",
            )
            self.db.add(comm)
            await self.db.commit()

            return AgentResult(
                success=True,
                data=result_data,
                tokens_input=tokens_in,
                tokens_output=tokens_out,
                message=f"Approval processed for {prescription.drug_name}. "
                        f"Revenue: ${revenue}. Ready to fill.",
            )

        except Exception as e:
            return AgentResult(
                success=False,
                error=f"Approval processing failed: {str(e)}",
                requires_human=True,
            )
