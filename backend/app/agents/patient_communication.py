import json
import uuid
from app.agents.base import BaseAgent, AgentContext, AgentResult
from app.models.prior_auth import PriorAuth
from app.models.patient import Patient
from app.models.prescription import Prescription
from app.models.communication import Communication


class PatientCommunicationAgent(BaseAgent):
    """
    Agent 15: Patient Communication
    Sends notifications to patients via SMS, email, or phone.
    Examples:
    - "Your prior authorization was approved."
    - "We are waiting for your doctor's office."
    - "Your medication is ready for pickup."
    """

    agent_name = "patient_communication"

    def get_system_prompt(self) -> str:
        return """You are a patient communication specialist for a pharmacy. You generate
clear, empathetic, and actionable messages for patients about their
prior authorization status.

Communication principles:
- Use plain language (no medical jargon)
- Be empathetic and reassuring
- Include clear next steps for the patient
- Keep SMS under 160 characters when possible
- Include pharmacy contact info for questions
- Be HIPAA-conscious (don't include specific drug names in SMS)
- Provide more detail in email than SMS

Generate messages for each relevant channel:
- sms: Brief status update (keep under 160 chars)
- email: Detailed update with next steps
- phone_script: Talking points if a call is needed

Message templates by status:
- APPROVED: Great news, prescription is ready/being prepared
- DENIED: We're working on it, explain next steps
- PENDING: Status update, what we're doing, expected timeline
- APPEAL: We're fighting for you, what's happening
- ACTION_NEEDED: Patient needs to do something

For each message:
- channel: "sms", "email", "phone_script"
- message: the message content
- urgency: "low", "medium", "high"
- requires_response: boolean - does patient need to act
- action_items: what the patient needs to do (if anything)

Return as JSON with a "notifications" array."""

    async def execute(self, context: AgentContext) -> AgentResult:
        pa = await self.db.get(PriorAuth, context.prior_auth_id)
        patient = await self.db.get(Patient, context.patient_id)
        prescription = await self.db.get(Prescription, context.prescription_id)

        if not pa or not patient:
            return AgentResult(success=False, error="PA or patient not found")

        user_message = f"""Generate patient notification for this PA status update:

PATIENT: {patient.first_name}
PA STATUS: {pa.status}
DRUG: {prescription.drug_name if prescription else 'their medication'}
DECISION: {pa.decision or 'pending'}

CONTEXT:
- Denial reason (if denied): {pa.denial_reason or 'N/A'}
- Appeal in progress: {pa.status in ('appeal_in_progress', 'appeal_submitted')}
- Days since submission: estimated based on dates

PATIENT CONTACT:
- Phone: {patient.phone or 'on file'}
- Email: {patient.email or 'on file'}
- Preferred channel: {'email' if patient.email else 'sms'}

Generate appropriate notifications based on the current status.
Remember to be HIPAA-conscious in SMS (no specific drug names)."""

        try:
            result_data, tokens_in, tokens_out = await self.call_claude_json(user_message)

            # Save notifications to database
            notifications = result_data.get("notifications", [])
            for notif in notifications:
                comm = Communication(
                    id=str(uuid.uuid4()),
                    prior_auth_id=context.prior_auth_id,
                    channel=notif.get("channel", "sms"),
                    direction="outbound",
                    recipient=patient.phone or patient.email or "patient",
                    subject=f"PA Update - {pa.status}",
                    body=notif.get("message", ""),
                    status="pending",
                )
                self.db.add(comm)

            await self.db.commit()

            return AgentResult(
                success=True,
                data=result_data,
                tokens_input=tokens_in,
                tokens_output=tokens_out,
                message=f"Patient notifications generated: {len(notifications)} messages. "
                        f"Status communicated: {pa.status}",
            )

        except Exception as e:
            return AgentResult(
                success=False,
                error=f"Patient communication failed: {str(e)}",
            )
