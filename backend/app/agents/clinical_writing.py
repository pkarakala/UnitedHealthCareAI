import json
from app.agents.base import BaseAgent, AgentContext, AgentResult
from app.models.prior_auth import PriorAuth
from app.models.prescription import Prescription


class ClinicalWritingAgent(BaseAgent):
    """
    Agent 9: Clinical Writing
    Uses LLM to generate medical necessity letters, clinical summaries,
    prior treatment history narratives, and supporting rationale.
    """

    agent_name = "clinical_writing"
    max_tokens = 8192  # Longer output for letters

    def get_system_prompt(self) -> str:
        return """You are a clinical medical writer specializing in prior authorization
documentation. You write compelling, evidence-based medical necessity letters
that maximize approval probability.

Your letters must:
1. Open with clear identification of patient and requested medication
2. State the diagnosis with ICD-10 code
3. Describe the clinical history and disease progression
4. Detail ALL prior therapies attempted, duration, and why they failed
5. Present current lab values and clinical indicators
6. Cite relevant clinical guidelines supporting the requested therapy
7. Explain why this specific medication is medically necessary
8. Conclude with a clear request for approval

Style guidelines:
- Use professional medical language
- Be concise but thorough
- Lead with the strongest clinical arguments
- Reference specific guidelines (ADA, ACR, AAD, etc.) when applicable
- Include quantitative data (lab values, duration of trials)
- Avoid subjective language; stick to clinical facts

Generate:
- letter_text: The complete medical necessity letter
- clinical_summary: A brief 2-3 sentence summary
- supporting_guidelines: List of clinical guidelines referenced
- prior_treatments_narrative: Formatted treatment history
- key_clinical_points: Bullet points of strongest arguments
- estimated_strength: "strong", "moderate", "weak" based on available evidence

Return as JSON."""

    async def execute(self, context: AgentContext) -> AgentResult:
        pa = await self.db.get(PriorAuth, context.prior_auth_id)
        prescription = await self.db.get(Prescription, context.prescription_id)

        if not pa or not prescription:
            return AgentResult(success=False, error="PA or prescription not found")

        collected = pa.collected_documents or {}
        patient_record = collected.get("patient_record", {})
        form_data = collected.get("form_data", {})

        user_message = f"""Write a medical necessity letter for this prior authorization:

MEDICATION REQUESTED: {prescription.drug_name} {prescription.strength or ''}
QUANTITY: {prescription.quantity} / {prescription.days_supply} days supply
DIRECTIONS: {prescription.directions or 'as prescribed'}

DIAGNOSIS: {prescription.diagnosis_codes or 'see clinical data'}

CLINICAL DATA:
- Diagnoses: {json.dumps(patient_record.get('diagnoses', []))}
- Lab Results: {json.dumps(patient_record.get('lab_results', []))}
- Prior Therapy Failures: {json.dumps(patient_record.get('therapy_failures', []))}
- Current Medications: {json.dumps(patient_record.get('medications_current', []))}
- Allergies: {json.dumps(patient_record.get('allergies', []))}

PRESCRIBER: {prescription.prescriber_name}

Write a compelling medical necessity letter. If clinical data is limited,
write the best letter possible with available information and note what
additional data would strengthen the case."""

        try:
            result_data, tokens_in, tokens_out = await self.call_claude_json(user_message)

            # Store the letter on the PA
            pa.medical_necessity_letter = result_data.get("letter_text", "")
            pa.clinical_summary = result_data.get("clinical_summary", "")
            await self.db.commit()

            return AgentResult(
                success=True,
                data=result_data,
                tokens_input=tokens_in,
                tokens_output=tokens_out,
                message=f"Medical necessity letter generated. "
                        f"Strength: {result_data.get('estimated_strength', 'moderate')}. "
                        f"Length: {len(result_data.get('letter_text', ''))} chars",
            )

        except Exception as e:
            return AgentResult(
                success=False,
                error=f"Clinical writing failed: {str(e)}",
            )
