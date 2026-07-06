import json
import uuid
from app.agents.base import BaseAgent, AgentContext, AgentResult
from app.models.prior_auth import PriorAuth
from app.models.prescription import Prescription
from app.models.appeal import Appeal


class AppealAgent(BaseAgent):
    """
    Agent 14: Appeal
    Drafts appeal letter with clinical guidelines, references, and evidence.
    Addresses the specific denial reason with targeted documentation.
    """

    agent_name = "appeal"
    max_tokens = 8192

    def get_system_prompt(self) -> str:
        return """You are a pharmacy prior authorization appeal specialist. You draft
compelling appeal letters that address the specific denial reason with
targeted clinical evidence.

Your appeal letters must:
1. Reference the specific denial reason and code
2. Directly address why the denial should be overturned
3. Cite relevant clinical practice guidelines (ADA, ACR, NCCN, etc.)
4. Include new or additional clinical evidence
5. Reference peer-reviewed literature when applicable
6. Document the medical necessity clearly
7. Request a specific action (overturn denial, approve PA)
8. Note the appeal deadline and any regulatory requirements

Appeal letter structure:
- Header: Patient info, PA number, date, appeal level
- Opening: Reference to denial and reason for appeal
- Clinical Argument: Why the medication is medically necessary
- Evidence: Prior therapies, labs, guidelines, literature
- Conclusion: Clear request for approval
- Enclosures: List of supporting documents

Generate:
- appeal_letter: Complete appeal letter text
- key_arguments: Top 3-5 arguments for overturn
- clinical_guidelines_cited: List of guidelines referenced
- literature_references: Relevant studies/publications
- additional_evidence_included: New evidence not in original submission
- recommended_enclosures: Documents to attach
- peer_to_peer_talking_points: If P2P review requested
- estimated_success_probability: float 0-1
- appeal_level: 1 (first level), 2 (external review), etc.

Return as JSON."""

    async def execute(self, context: AgentContext) -> AgentResult:
        pa = await self.db.get(PriorAuth, context.prior_auth_id)
        prescription = await self.db.get(Prescription, context.prescription_id)

        if not pa or not prescription:
            return AgentResult(success=False, error="PA or prescription not found")

        denial_analysis = {}
        if pa.denial_codes and "analysis" in pa.denial_codes:
            denial_analysis = pa.denial_codes["analysis"]

        collected = pa.collected_documents or {}
        patient_record = collected.get("patient_record", {})

        user_message = f"""Draft an appeal letter for this denied PA:

DRUG: {prescription.drug_name} {prescription.strength or ''}
ORIGINAL DENIAL REASON: {pa.denial_reason or 'Not specified'}
DENIAL CATEGORY: {denial_analysis.get('denial_category', 'unknown')}
ROOT CAUSE: {denial_analysis.get('root_cause', 'unknown')}
RECOMMENDED STRATEGY: {denial_analysis.get('recommended_strategy', 'standard appeal')}
ADDITIONAL EVIDENCE NEEDED: {json.dumps(denial_analysis.get('additional_evidence_needed', []))}

ORIGINAL MEDICAL NECESSITY LETTER:
{pa.medical_necessity_letter[:500] if pa.medical_necessity_letter else 'Not available'}

PATIENT CLINICAL DATA:
- Diagnoses: {json.dumps(patient_record.get('diagnoses', []))}
- Prior Therapies: {json.dumps(patient_record.get('therapy_failures', []))}
- Labs: {json.dumps(patient_record.get('lab_results', []))}

Draft a compelling appeal letter that directly addresses the denial reason
and provides additional clinical justification."""

        try:
            result_data, tokens_in, tokens_out = await self.call_claude_json(user_message)

            # Create appeal record
            appeal = Appeal(
                id=str(uuid.uuid4()),
                prior_auth_id=context.prior_auth_id,
                level=denial_analysis.get("appeal_level", 1),
                status="draft",
                denial_reason=pa.denial_reason,
                denial_codes=pa.denial_codes,
                appeal_strategy=denial_analysis.get("recommended_strategy"),
                appeal_letter=result_data.get("appeal_letter", ""),
                supporting_evidence=result_data.get("additional_evidence_included"),
                clinical_references=result_data.get("literature_references"),
            )
            self.db.add(appeal)

            pa.status = "appeal_in_progress"
            await self.db.commit()

            return AgentResult(
                success=True,
                data=result_data,
                tokens_input=tokens_in,
                tokens_output=tokens_out,
                message=f"Appeal letter drafted. "
                        f"Key arguments: {len(result_data.get('key_arguments', []))}. "
                        f"Estimated success: {result_data.get('estimated_success_probability', 0)*100:.0f}%",
            )

        except Exception as e:
            return AgentResult(
                success=False,
                error=f"Appeal drafting failed: {str(e)}",
                requires_human=True,
            )
