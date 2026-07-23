import json
from app.agents.base import BaseAgent, AgentContext, AgentResult
from app.models.insurance import Insurance
from app.models.patient import Patient


class InsuranceVerificationAgent(BaseAgent):
    """
    Agent 3: Insurance Verification
    Verifies patient insurance eligibility and coverage details.
    Checks BIN, PCN, Group, Member ID, active status, preferred drug status.
    Also detects step therapy, quantity limits, age/diagnosis restrictions.
    """

    agent_name = "insurance_verification"
    simulates_external_calls = True  # No real eligibility API — coverage/copay is LLM-guessed

    def get_system_prompt(self) -> str:
        return """You are a pharmacy insurance verification specialist. Your job is to verify
patient insurance eligibility and coverage details for prescription medications.

You analyze:
1. Member ID validity
2. Coverage active status
3. Plan type and benefits
4. Drug coverage tier
5. Step therapy requirements
6. Quantity limits
7. Age restrictions
8. Diagnosis-specific requirements
9. Preferred pharmacy status
10. Copay/coinsurance information

Given the patient and insurance information, provide a verification result:
- is_active: boolean - is coverage active
- plan_name: string - verified plan name
- coverage_type: string - "commercial", "medicare", "medicaid", "workers_comp"
- drug_tier: string - "tier1_generic", "tier2_preferred", "tier3_nonpreferred", "tier4_specialty"
- copay_estimate: float - estimated copay amount
- deductible_remaining: float - remaining deductible if known
- step_therapy_required: boolean
- step_therapy_drugs: list - drugs that must be tried first
- quantity_limit_applies: boolean
- max_quantity_allowed: int or null
- age_restriction: boolean
- diagnosis_restriction: boolean
- required_diagnosis_codes: list - ICD-10 codes needed
- prior_auth_form: string - which PA form to use
- submission_method: string - "epa", "covermymeds", "fax", "portal"
- portal_url: string or null
- notes: string - any additional findings

Return as JSON."""

    async def execute(self, context: AgentContext) -> AgentResult:
        patient = await self.db.get(Patient, context.patient_id)
        if not patient:
            return AgentResult(success=False, error="Patient not found")

        insurance = None
        if context.insurance_id:
            insurance = await self.db.get(Insurance, context.insurance_id)

        patient_info = {
            "member_id": patient.member_id,
            "group_number": patient.group_number,
            "date_of_birth": str(patient.date_of_birth) if patient.date_of_birth else None,
        }

        insurance_info = {}
        if insurance:
            insurance_info = {
                "plan_name": insurance.plan_name,
                "payer_name": insurance.payer_name,
                "bin_number": insurance.bin_number,
                "pcn": insurance.pcn,
                "group_number": insurance.group_number,
                "is_active": insurance.is_active,
                "portal_url": insurance.portal_url,
                "formulary_data": insurance.formulary_data,
                "step_therapy_rules": insurance.step_therapy_rules,
                "quantity_limits": insurance.quantity_limits,
            }

        user_message = f"""Verify insurance eligibility and coverage for this patient:

PATIENT:
{json.dumps(patient_info, indent=2)}

INSURANCE PLAN:
{json.dumps(insurance_info, indent=2) if insurance_info else 'No insurance record found - flag for manual verification'}

Verify coverage status and identify any restrictions or requirements that will
affect the prior authorization process."""

        try:
            result_data, tokens_in, tokens_out = await self.call_claude_json(user_message)

            is_active = result_data.get("is_active", True)
            condition = "verified" if is_active else "failed"

            # Update insurance record with verification findings
            if insurance and result_data.get("step_therapy_required"):
                insurance.step_therapy_rules = dict(insurance.step_therapy_rules or {})
                insurance.step_therapy_rules["verified"] = True
                insurance.step_therapy_rules["drugs"] = result_data.get("step_therapy_drugs", [])

            await self.mark_simulated(context.prior_auth_id)
            await self.db.commit()

            return AgentResult(
                success=True,
                data=result_data,
                condition=condition,
                tokens_input=tokens_in,
                tokens_output=tokens_out,
                message=f"Insurance verification {'passed' if is_active else 'failed'}. "
                        f"Plan: {result_data.get('plan_name', 'Unknown')}",
            )

        except Exception as e:
            return AgentResult(
                success=False,
                error=f"Insurance verification failed: {str(e)}",
                condition="verified",  # Continue workflow even on error
            )
