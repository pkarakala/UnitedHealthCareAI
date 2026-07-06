import json
from app.agents.base import BaseAgent, AgentContext, AgentResult
from app.models.prior_auth import PriorAuth
from app.models.prescription import Prescription
from app.models.patient import Patient
from app.models.insurance import Insurance


class PAFormFillingAgent(BaseAgent):
    """
    Agent 8: PA Form Filling
    Automatically fills PA forms for CoverMyMeds, ePA portals, insurance portals.
    Maps patient/drug/clinical data to form fields.
    This alone saves several minutes per PA.
    """

    agent_name = "pa_form_filling"

    def get_system_prompt(self) -> str:
        return """You are a prior authorization form completion specialist. You map clinical
and patient data to PA form fields accurately and completely.

PA forms typically require:
SECTION 1 - PATIENT INFORMATION:
- Patient name, DOB, address, phone
- Member ID, Group number
- Insurance plan information

SECTION 2 - PRESCRIBER INFORMATION:
- Physician name, NPI, address, phone, fax
- Specialty
- Tax ID

SECTION 3 - MEDICATION INFORMATION:
- Drug name, strength, dosage form
- Quantity, days supply, refills
- Directions for use
- Start date

SECTION 4 - CLINICAL INFORMATION:
- Diagnosis (ICD-10)
- Clinical rationale
- Previous medications tried and failed
- Lab results supporting the request
- Duration of current condition

SECTION 5 - SUPPORTING DOCUMENTATION:
- Attached documents checklist
- Additional notes

For the given PA, generate a complete form filling map:
- form_data: dict mapping field names to values
- submission_platform: "covermymeds", "epa", "insurance_portal", "fax"
- attachments_needed: list of documents to attach
- missing_fields: any fields we cannot fill
- ready_to_submit: boolean
- confidence: float - how complete the form is

Return as JSON."""

    async def execute(self, context: AgentContext) -> AgentResult:
        pa = await self.db.get(PriorAuth, context.prior_auth_id)
        prescription = await self.db.get(Prescription, context.prescription_id)
        patient = await self.db.get(Patient, context.patient_id)

        if not all([pa, prescription, patient]):
            return AgentResult(success=False, error="Required records not found")

        insurance = None
        if context.insurance_id:
            insurance = await self.db.get(Insurance, context.insurance_id)

        collected_data = pa.collected_documents or {}
        patient_record = collected_data.get("patient_record", {})

        user_message = f"""Fill out the PA form with available data:

PATIENT:
- Name: {patient.first_name} {patient.last_name}
- DOB: {patient.date_of_birth}
- Phone: {patient.phone or 'on file'}
- Member ID: {patient.member_id}
- Group: {patient.group_number}
- Address: {json.dumps(patient.address) if patient.address else 'on file'}

PRESCRIBER:
- Name: {prescription.prescriber_name}
- NPI: {prescription.prescriber_npi}
- Phone: {prescription.prescriber_phone or 'on file'}
- Fax: {prescription.prescriber_fax or 'on file'}

MEDICATION:
- Drug: {prescription.drug_name}
- Strength: {prescription.strength}
- Quantity: {prescription.quantity}
- Days Supply: {prescription.days_supply}
- Directions: {prescription.directions}
- Refills: {prescription.refills}

INSURANCE:
- Plan: {insurance.plan_name if insurance else 'on file'}
- BIN: {insurance.bin_number if insurance else ''}
- PCN: {insurance.pcn if insurance else ''}
- Payer: {insurance.payer_name if insurance else ''}

CLINICAL DATA:
- Diagnosis Codes: {prescription.diagnosis_codes or 'pending'}
- Clinical Record: {json.dumps(patient_record.get('diagnoses', [])) if patient_record else 'pending'}
- Lab Results: {json.dumps(patient_record.get('lab_results', [])) if patient_record else 'pending'}
- Prior Therapies: {json.dumps(patient_record.get('therapy_failures', [])) if patient_record else 'pending'}

REQUIRED DOCUMENTATION: {json.dumps(pa.required_documents) if pa.required_documents else 'standard'}

Map all available data to PA form fields. Identify the best submission platform."""

        try:
            result_data, tokens_in, tokens_out = await self.call_claude_json(user_message)

            # Store form data on PA
            pa.submission_method = result_data.get("submission_platform", "covermymeds")
            pa.collected_documents = pa.collected_documents or {}
            pa.collected_documents["form_data"] = result_data.get("form_data", {})
            await self.db.commit()

            return AgentResult(
                success=True,
                data=result_data,
                tokens_input=tokens_in,
                tokens_output=tokens_out,
                message=f"PA form filled via {result_data.get('submission_platform', 'covermymeds')}. "
                        f"Completeness: {result_data.get('confidence', 0)*100:.0f}%",
            )

        except Exception as e:
            return AgentResult(
                success=False,
                error=f"Form filling failed: {str(e)}",
            )
