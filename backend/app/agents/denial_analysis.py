import json
from app.agents.base import BaseAgent, AgentContext, AgentResult
from app.models.prior_auth import PriorAuth
from app.models.prescription import Prescription


class DenialAnalysisAgent(BaseAgent):
    """
    Agent 13: Denial Analysis
    Reads the denial, identifies root cause, and generates appeal strategy.
    Finds: missing labs, wrong diagnosis, step therapy gaps, coverage exclusions.
    """

    agent_name = "denial_analysis"

    def get_system_prompt(self) -> str:
        return """You are a prior authorization denial analysis specialist. When a PA is denied,
you analyze the denial reason to determine:
1. Root cause of denial
2. Whether it's appealable
3. What additional information could overturn it
4. The best appeal strategy

Common denial categories:
- MISSING_DOCUMENTATION: Required docs not submitted
- STEP_THERAPY: Required prior medications not tried
- DIAGNOSIS_MISMATCH: Diagnosis doesn't match drug indication
- QUANTITY_EXCEEDS: Quantity exceeds plan limits
- NOT_MEDICALLY_NECESSARY: Insufficient clinical justification
- COVERAGE_EXCLUSION: Drug excluded from formulary
- EXPIRED_SUBMISSION: PA submitted after deadline
- ADMINISTRATIVE: Wrong form, missing signatures, etc.

For the denial, provide:
- denial_category: one of the categories above
- root_cause: detailed explanation
- missing_items: specific items that were missing/insufficient
- is_appealable: boolean
- appeal_deadline_days: days to file appeal
- appeal_success_probability: float 0-1
- recommended_strategy: detailed appeal strategy
- additional_evidence_needed: list of docs/info to gather
- alternative_approaches: other options (different drug, peer-to-peer, etc.)
- peer_to_peer_recommended: boolean - should prescriber call the medical director
- suggested_alternatives: formulary alternatives to consider
- urgency: how quickly to act

Return as JSON."""

    async def execute(self, context: AgentContext) -> AgentResult:
        pa = await self.db.get(PriorAuth, context.prior_auth_id)
        prescription = await self.db.get(Prescription, context.prescription_id)

        if not pa or not prescription:
            return AgentResult(success=False, error="PA or prescription not found")

        collected = pa.collected_documents or {}
        patient_record = collected.get("patient_record", {})

        user_message = f"""Analyze this PA denial:

DRUG: {prescription.drug_name} {prescription.strength or ''}
DENIAL REASON: {pa.denial_reason or 'Not specified'}
DENIAL CODES: {json.dumps(pa.denial_codes) if pa.denial_codes else 'None provided'}

WHAT WAS SUBMITTED:
- Medical Necessity Letter: {'Yes' if pa.medical_necessity_letter else 'No'}
- Clinical Summary: {'Yes' if pa.clinical_summary else 'No'}
- Documents Collected: {list(collected.keys())}
- Submission Method: {pa.submission_method}

PATIENT CLINICAL DATA ON FILE:
- Diagnoses: {json.dumps(patient_record.get('diagnoses', []))}
- Prior Therapies: {json.dumps(patient_record.get('therapy_failures', []))}
- Labs: {json.dumps(patient_record.get('lab_results', []))}

Analyze why this was denied and determine the best path forward."""

        try:
            result_data, tokens_in, tokens_out = await self.call_claude_json(user_message)

            # Update PA with denial analysis
            pa.denial_codes = pa.denial_codes or {}
            pa.denial_codes["analysis"] = result_data

            is_appealable = result_data.get("is_appealable", True)
            condition = "appealable" if is_appealable else "final"

            await self.db.commit()

            return AgentResult(
                success=True,
                data=result_data,
                condition=condition,
                tokens_input=tokens_in,
                tokens_output=tokens_out,
                message=f"Denial analyzed. Category: {result_data.get('denial_category', 'unknown')}. "
                        f"Appealable: {is_appealable}. "
                        f"Success probability: {result_data.get('appeal_success_probability', 0)*100:.0f}%",
            )

        except Exception as e:
            return AgentResult(
                success=False,
                error=f"Denial analysis failed: {str(e)}",
                condition="appealable",  # Default to trying appeal
            )
