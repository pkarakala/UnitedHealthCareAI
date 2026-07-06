import json
from app.agents.base import BaseAgent, AgentContext, AgentResult
from app.models.prior_auth import PriorAuth
from app.models.prescription import Prescription
from app.models.patient import Patient


class PatientRecordAgent(BaseAgent):
    """
    Agent 5: Patient Record Retrieval
    Collects clinical data from available sources:
    - Medication history and fill history
    - Allergies
    - Previous therapy failures
    - ICD-10 codes
    - Lab values
    - Progress notes
    Sources: Pharmacy Management System, EHR, Health Information Exchange.
    """

    agent_name = "patient_record"

    def get_system_prompt(self) -> str:
        return """You are a patient medical records retrieval specialist. Your job is to
compile a comprehensive clinical profile from available patient data sources.

You gather:
1. Current and past medications (fill history from pharmacy system)
2. Allergies and adverse reactions
3. Diagnosis history (ICD-10 codes)
4. Lab results (with dates and values)
5. Previous PA attempts and outcomes
6. Clinical notes relevant to the current PA
7. Specialist referrals and evaluations

For each piece of data, note:
- The source (pharmacy system, EHR, HIE, patient-reported)
- The date of the record
- Relevance to the current PA request

Compile into a structured clinical profile:
- medications_current: list of current meds with start dates
- medications_history: list of past meds (especially relevant prior therapies)
- allergies: list of allergies/intolerances
- diagnoses: list of {code, description, date_diagnosed}
- lab_results: list of {test_name, value, unit, date, normal_range}
- prior_auth_history: list of previous PA attempts
- therapy_failures: list of {drug, duration, reason_discontinued}
- clinical_notes_summary: relevant progress note excerpts
- data_gaps: what information we couldn't find

Return as JSON."""

    async def execute(self, context: AgentContext) -> AgentResult:
        patient = await self.db.get(Patient, context.patient_id)
        prescription = await self.db.get(Prescription, context.prescription_id)
        pa = await self.db.get(PriorAuth, context.prior_auth_id)

        if not patient or not prescription:
            return AgentResult(success=False, error="Patient or prescription not found")

        required_docs = pa.required_documents if pa else []

        user_message = f"""Compile the clinical record for this patient in context of their PA request.

PATIENT: {patient.first_name} {patient.last_name}
DOB: {patient.date_of_birth}

CURRENT PRESCRIPTION NEEDING PA:
- Drug: {prescription.drug_name} {prescription.strength or ''}
- Diagnosis codes on Rx: {prescription.diagnosis_codes or 'none'}

DOCUMENTATION NEEDED FOR PA:
{json.dumps(required_docs, indent=2) if required_docs else 'General clinical profile needed'}

AVAILABLE DATA SOURCES (simulated):
- Pharmacy Management System: Fill history for past 24 months
- Patient demographics and insurance on file
- Any previously uploaded clinical documents

Based on what's typically available in a pharmacy setting, compile what we have
and identify what we need from the prescriber's office.

Note: In production, this agent would query actual pharmacy systems, EHR integrations,
and Health Information Exchanges. For now, generate a realistic clinical profile
based on the drug being prescribed and typical patient scenarios."""

        try:
            result_data, tokens_in, tokens_out = await self.call_claude_json(user_message)

            # Update PA with collected data
            if pa:
                pa.collected_documents = pa.collected_documents or {}
                pa.collected_documents["patient_record"] = result_data
                await self.db.commit()

            data_gaps = result_data.get("data_gaps", [])
            has_gaps = len(data_gaps) > 0

            return AgentResult(
                success=True,
                data=result_data,
                condition="records_missing" if has_gaps else "records_found",
                tokens_input=tokens_in,
                tokens_output=tokens_out,
                message=f"Patient records compiled. "
                        f"{'Data gaps: ' + ', '.join(data_gaps[:3]) if has_gaps else 'Record complete.'}",
            )

        except Exception as e:
            return AgentResult(
                success=False,
                error=f"Patient record retrieval failed: {str(e)}",
                condition="records_missing",
            )
