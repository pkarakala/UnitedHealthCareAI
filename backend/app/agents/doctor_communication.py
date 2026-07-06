import json
from app.agents.base import BaseAgent, AgentContext, AgentResult
from app.models.prescription import Prescription
from app.models.prior_auth import PriorAuth
from app.models.communication import Communication


class DoctorCommunicationAgent(BaseAgent):
    """
    Agent 6: Doctor Communication
    Generates outreach messages to prescriber offices requesting missing documentation.
    Produces: fax cover sheets, portal messages, phone scripts, emails.
    This is where pharmacies spend enormous amounts of time manually.
    """

    agent_name = "doctor_communication"

    def get_system_prompt(self) -> str:
        return """You are a pharmacy-to-prescriber communication specialist. You generate
professional, clear, and actionable outreach messages requesting clinical documentation
needed for prior authorization.

Your communications must be:
- Professional and respectful of the prescriber's time
- Specific about what documentation is needed
- Clear about deadlines and urgency
- Include patient identifiers for easy lookup
- Provide multiple response options (fax back, portal, phone)

Generate communications for each requested channel:
- fax: Formal fax cover letter with checkbox list of needed items
- email: Concise email with clear ask and deadline
- portal: Brief portal message suitable for EHR messaging
- phone_script: Talking points for a phone call to the office

For each communication, provide:
- channel: the communication method
- subject: subject line or header
- body: full message text
- urgency: "routine", "urgent", "stat"
- expected_response_days: typical response time for this channel

Return as JSON with a "communications" array."""

    async def execute(self, context: AgentContext) -> AgentResult:
        prescription = await self.db.get(Prescription, context.prescription_id)
        pa = await self.db.get(PriorAuth, context.prior_auth_id)

        if not prescription or not pa:
            return AgentResult(success=False, error="Prescription or PA not found")

        # Determine what's missing
        required = pa.required_documents or []
        collected = pa.collected_documents or {}
        patient_record = collected.get("patient_record", {})
        data_gaps = patient_record.get("data_gaps", required)

        user_message = f"""Generate prescriber outreach for this prior authorization:

PATIENT: (name on file)
PRESCRIBER: {prescription.prescriber_name or 'Prescriber'}
PRESCRIBER NPI: {prescription.prescriber_npi}
PRESCRIBER FAX: {prescription.prescriber_fax or 'on file'}
PRESCRIBER PHONE: {prescription.prescriber_phone or 'on file'}

MEDICATION: {prescription.drug_name} {prescription.strength or ''}
QUANTITY: {prescription.quantity} / {prescription.days_supply} days

PRIOR AUTHORIZATION REQUIRED FOR:
{json.dumps(data_gaps, indent=2) if data_gaps else 'General clinical documentation'}

SPECIFIC ITEMS NEEDED FROM PRESCRIBER:
1. Diagnosis confirmation with ICD-10 code
2. Relevant lab results (if applicable)
3. Prior medication history and reasons for failure
4. Clinical notes supporting medical necessity
5. Any other documentation per payer requirements

Generate professional communications for fax, email, and phone script channels.
The fax should be a complete cover letter with a checklist the office can mark up and fax back."""

        try:
            result_data, tokens_in, tokens_out = await self.call_claude_json(user_message)

            # Save communications to database
            communications = result_data.get("communications", [])
            for comm_data in communications:
                comm = Communication(
                    prior_auth_id=context.prior_auth_id,
                    channel=comm_data.get("channel", "fax"),
                    direction="outbound",
                    recipient=prescription.prescriber_name or "Prescriber",
                    subject=comm_data.get("subject", "PA Documentation Request"),
                    body=comm_data.get("body", ""),
                    status="pending",
                )
                self.db.add(comm)

            pa.sub_status = "awaiting_prescriber_response"
            await self.db.commit()

            return AgentResult(
                success=True,
                data=result_data,
                condition="awaiting_response",
                tokens_input=tokens_in,
                tokens_output=tokens_out,
                message=f"Generated {len(communications)} outreach messages to prescriber. "
                        f"Awaiting response for: {', '.join(data_gaps[:3]) if data_gaps else 'documentation'}",
            )

        except Exception as e:
            return AgentResult(
                success=False,
                error=f"Doctor communication generation failed: {str(e)}",
                condition="awaiting_response",
            )
