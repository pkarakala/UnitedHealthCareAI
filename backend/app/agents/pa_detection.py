import json
from sqlalchemy import select

from app.agents.base import BaseAgent, AgentContext, AgentResult
from app.models.prescription import Prescription
from app.models.insurance import Insurance


class PADetectionAgent(BaseAgent):
    """
    Agent 2: PA Detection
    Determines whether prior authorization is required for a prescription.
    Checks reject codes, DUR messages, NCPDP responses, plan formulary.
    """

    agent_name = "pa_detection"

    def get_system_prompt(self) -> str:
        return """You are a pharmacy prior authorization detection specialist. Your job is to
determine whether a prescription requires prior authorization.

You analyze:
1. NCPDP reject codes (75 = PA required, 76 = plan limitations)
2. DUR (Drug Utilization Review) messages
3. Plan formulary status (non-preferred, specialty tier, excluded)
4. Step therapy requirements
5. Quantity limits that exceed standard coverage
6. Age or diagnosis restrictions

Based on the prescription and insurance data provided, determine:
- pa_required: boolean - whether PA is needed
- reason: string - why PA is/isn't required
- reject_codes: list - relevant reject codes
- formulary_status: string - "preferred", "non_preferred", "specialty", "excluded"
- step_therapy_required: boolean
- quantity_limit_exceeded: boolean
- alternatives: list - preferred formulary alternatives if available
- urgency: string - "routine", "urgent", "emergency"
- confidence: float - your confidence in this determination (0.0-1.0)

Return as JSON."""

    async def execute(self, context: AgentContext) -> AgentResult:
        prescription = await self.db.get(Prescription, context.prescription_id)
        if not prescription:
            return AgentResult(success=False, error="Prescription not found")

        # Load insurance data if available
        insurance_data = {}
        if context.insurance_id:
            insurance = await self.db.get(Insurance, context.insurance_id)
            if insurance:
                insurance_data = {
                    "plan_name": insurance.plan_name,
                    "payer_name": insurance.payer_name,
                    "formulary_data": insurance.formulary_data,
                    "pa_requirements": insurance.pa_requirements,
                    "step_therapy_rules": insurance.step_therapy_rules,
                    "quantity_limits": insurance.quantity_limits,
                }

        user_message = f"""Determine if prior authorization is required for this prescription:

PRESCRIPTION:
- Drug: {prescription.drug_name}
- Strength: {prescription.strength}
- Quantity: {prescription.quantity}
- Days Supply: {prescription.days_supply}
- Diagnosis Codes: {prescription.diagnosis_codes or 'not provided'}

INSURANCE:
{json.dumps(insurance_data, indent=2) if insurance_data else 'No insurance data available - assume PA likely required for specialty/non-preferred drugs'}

COMMON PA-REQUIRED DRUGS (reference):
- GLP-1 agonists (Ozempic, Wegovy, Mounjaro, Zepbound)
- Specialty biologics (Humira, Enbrel, Stelara)
- PCSK9 inhibitors (Repatha, Praluent)
- Oral oncology drugs
- High-cost brand medications without generic alternatives

Analyze and determine PA requirement."""

        try:
            result_data, tokens_in, tokens_out = await self.call_claude_json(user_message)

            pa_required = result_data.get("pa_required", True)
            condition = "pa_required" if pa_required else "not_required"

            return AgentResult(
                success=True,
                data=result_data,
                condition=condition,
                tokens_input=tokens_in,
                tokens_output=tokens_out,
                message=f"PA {'required' if pa_required else 'not required'} for {prescription.drug_name}. "
                        f"Reason: {result_data.get('reason', 'N/A')}",
            )

        except Exception as e:
            return AgentResult(
                success=False,
                error=f"PA detection failed: {str(e)}",
                condition="pa_required",  # Default to PA required on error (safe path)
            )
