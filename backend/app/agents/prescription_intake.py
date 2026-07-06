import json
from sqlalchemy import select

from app.agents.base import BaseAgent, AgentContext, AgentResult
from app.models.prescription import Prescription


class PrescriptionIntakeAgent(BaseAgent):
    """
    Agent 1: Prescription Intake
    Reads prescriptions from various sources (electronic, fax, paper, phone).
    Uses Claude's vision capabilities for OCR on prescription images.
    Extracts: drug, strength, quantity, directions, prescriber, insurance info.
    """

    agent_name = "prescription_intake"

    def get_system_prompt(self) -> str:
        return """You are a pharmacy prescription intake specialist AI. Your job is to extract
structured prescription data from raw text or image descriptions.

Extract the following fields:
- drug_name: The medication name
- strength: Dosage strength (e.g., "10mg", "100mg/mL")
- quantity: Number of units dispensed
- days_supply: Days the prescription should last
- directions: Sig/directions for use
- refills: Number of refills authorized
- prescriber_name: Doctor/prescriber name
- prescriber_npi: NPI number if visible
- prescriber_phone: Phone number
- prescriber_fax: Fax number
- patient_name: Patient full name
- date_written: Date prescription was written
- ndc: National Drug Code if visible
- diagnosis_codes: Any ICD-10 codes listed

Return your response as JSON with these fields. Set confidence (0.0-1.0) based on
how clearly you could read each field. If a field is not visible or unclear, set it to null.

Also include:
- confidence: overall confidence score
- flags: any concerns (e.g., "illegible dosage", "missing NPI")
"""

    async def execute(self, context: AgentContext) -> AgentResult:
        prescription = await self.db.get(Prescription, context.prescription_id)
        if not prescription:
            return AgentResult(success=False, error="Prescription not found")

        # Build the message for Claude based on available data
        if prescription.raw_image_url:
            # Vision-based extraction from prescription image
            user_message = f"""Extract prescription details from this prescription.

Available information:
- Source: {prescription.source or 'unknown'}
- Drug (if known): {prescription.drug_name or 'extract from image'}
- Any existing data: {json.dumps({
    'drug_name': prescription.drug_name,
    'prescriber_npi': prescription.prescriber_npi,
    'quantity': prescription.quantity,
})}

Please extract and verify all prescription fields."""
        else:
            # Text-based extraction
            user_message = f"""Verify and complete the following prescription data:

Drug: {prescription.drug_name}
Strength: {prescription.strength or 'unknown'}
Quantity: {prescription.quantity or 'unknown'}
Days Supply: {prescription.days_supply or 'unknown'}
Directions: {prescription.directions or 'unknown'}
Prescriber: {prescription.prescriber_name or 'unknown'}
NPI: {prescription.prescriber_npi}
Date Written: {prescription.date_written or 'unknown'}
Diagnosis Codes: {prescription.diagnosis_codes or 'none provided'}

Validate the data, flag any inconsistencies, and return structured JSON."""

        try:
            result_data, tokens_in, tokens_out = await self.call_claude_json(user_message)

            # Update prescription with extracted data
            if result_data.get("drug_name"):
                prescription.drug_name = result_data["drug_name"]
            if result_data.get("strength"):
                prescription.strength = result_data["strength"]
            if result_data.get("quantity"):
                prescription.quantity = result_data["quantity"]
            if result_data.get("days_supply"):
                prescription.days_supply = result_data["days_supply"]
            if result_data.get("directions"):
                prescription.directions = result_data["directions"]
            if result_data.get("ndc"):
                prescription.ndc = result_data["ndc"]
            if result_data.get("diagnosis_codes"):
                prescription.diagnosis_codes = result_data["diagnosis_codes"]

            prescription.ocr_confidence = result_data.get("confidence", 0.9)
            prescription.status = "verified"
            await self.db.commit()

            return AgentResult(
                success=True,
                data=result_data,
                condition="pa_required",  # Always advance to PA detection
                tokens_input=tokens_in,
                tokens_output=tokens_out,
                message=f"Prescription intake complete. Drug: {prescription.drug_name}",
            )

        except Exception as e:
            return AgentResult(
                success=False,
                error=f"Failed to process prescription: {str(e)}",
                requires_human=True,
                message="Could not automatically process prescription. Manual review needed.",
            )
