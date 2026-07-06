import json
from app.agents.base import BaseAgent, AgentContext, AgentResult
from app.models.prescription import Prescription
from app.models.prior_auth import PriorAuth
from app.models.insurance import Insurance


class ClinicalRequirementAgent(BaseAgent):
    """
    Agent 4: Clinical Requirement
    Reads payer-specific PA requirements for the drug.
    Determines what clinical documentation is needed.
    Example: Ozempic requires Type 2 diabetes diagnosis, HbA1c, metformin failure.
    """

    agent_name = "clinical_requirement"

    def get_system_prompt(self) -> str:
        return """You are a clinical requirements analyst for pharmacy prior authorizations.
Your expertise is in knowing what documentation insurance companies require for PA approval.

For each drug, you know the typical requirements:
- Required diagnoses (ICD-10 codes)
- Required lab values (HbA1c, liver function, renal function, etc.)
- Step therapy / prior medication failures required
- Duration of prior therapy attempts
- Specific clinical criteria

COMMON DRUG REQUIREMENTS (reference):
- Ozempic/Wegovy: Type 2 diabetes (E11.x), HbA1c > 7%, metformin trial 3+ months
- Humira: RA/Psoriasis/Crohn's diagnosis, DMARD failure, labs
- Dupixent: Moderate-severe atopic dermatitis, topical steroid failure
- Xeljanz: RA diagnosis, MTX failure, specific labs
- Repatha: LDL > 70 on max statin, ASCVD or FH diagnosis
- Entresto: Heart failure (NYHA II-IV), current ACE/ARB use
- Specialty oncology: Confirmed diagnosis, staging, prior treatment history

Given the drug and payer, determine:
- required_diagnoses: list of ICD-10 codes/descriptions needed
- required_labs: list of lab tests and acceptable values
- required_prior_therapies: list of drugs that must have been tried
- min_therapy_duration: minimum days on prior therapy
- additional_documentation: other docs needed (progress notes, specialist letter)
- missing_items: what we DON'T yet have (based on available patient data)
- documentation_checklist: complete checklist for PA submission
- complexity: "simple", "moderate", "complex"
- estimated_approval_probability: float 0-1 if all docs obtained

Return as JSON."""

    async def execute(self, context: AgentContext) -> AgentResult:
        prescription = await self.db.get(Prescription, context.prescription_id)
        pa = await self.db.get(PriorAuth, context.prior_auth_id)

        if not prescription or not pa:
            return AgentResult(success=False, error="Prescription or PA not found")

        insurance = None
        if context.insurance_id:
            insurance = await self.db.get(Insurance, context.insurance_id)

        user_message = f"""Determine the clinical documentation requirements for this PA:

DRUG: {prescription.drug_name}
STRENGTH: {prescription.strength or 'not specified'}
DIAGNOSIS CODES ON FILE: {prescription.diagnosis_codes or 'none'}

INSURANCE PLAN: {insurance.plan_name if insurance else 'Unknown'}
PAYER: {insurance.payer_name if insurance else 'Unknown'}
PLAN PA REQUIREMENTS: {json.dumps(insurance.pa_requirements) if insurance and insurance.pa_requirements else 'not on file'}

PATIENT DATA CURRENTLY AVAILABLE:
- Diagnosis codes: {prescription.diagnosis_codes or 'none'}
- Previously collected docs: {pa.collected_documents or 'none'}

What documentation is required for PA approval? What is missing?"""

        try:
            result_data, tokens_in, tokens_out = await self.call_claude_json(user_message)

            # Update PA with requirements
            pa.required_documents = result_data.get("documentation_checklist", [])
            await self.db.commit()

            # Determine if we need more docs or can proceed
            missing = result_data.get("missing_items", [])
            condition = "docs_needed" if missing else "docs_complete"

            return AgentResult(
                success=True,
                data=result_data,
                condition=condition,
                tokens_input=tokens_in,
                tokens_output=tokens_out,
                message=f"Clinical requirements analyzed. "
                        f"{'Missing: ' + ', '.join(missing[:3]) if missing else 'All documentation available.'}",
            )

        except Exception as e:
            return AgentResult(
                success=False,
                error=f"Clinical requirement analysis failed: {str(e)}",
                condition="docs_needed",  # Safe default
            )
