import structlog
from dataclasses import dataclass
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.prior_auth import PriorAuth
from app.utils.constants import PAStatus
from app.agents.base import BaseAgent, AgentContext, AgentResult

logger = structlog.get_logger()


@dataclass
class Transition:
    next_status: PAStatus
    agent_name: str | None
    condition: str | None = None


WORKFLOW_TRANSITIONS: dict[PAStatus, list[Transition]] = {
    PAStatus.INTAKE: [
        Transition(next_status=PAStatus.PA_DETECTION, agent_name="pa_detection"),
    ],
    PAStatus.PA_DETECTION: [
        Transition(
            next_status=PAStatus.INSURANCE_VERIFICATION,
            agent_name="insurance_verification",
            condition="pa_required",
        ),
        Transition(
            next_status=PAStatus.NO_PA_REQUIRED,
            agent_name=None,
            condition="not_required",
        ),
    ],
    PAStatus.NO_PA_REQUIRED: [
        Transition(next_status=PAStatus.COMPLETED, agent_name="patient_communication"),
    ],
    PAStatus.INSURANCE_VERIFICATION: [
        Transition(
            next_status=PAStatus.CLINICAL_REVIEW,
            agent_name="clinical_requirement",
            condition="verified",
        ),
        Transition(
            next_status=PAStatus.ERROR,
            agent_name=None,
            condition="failed",
        ),
    ],
    PAStatus.CLINICAL_REVIEW: [
        Transition(
            next_status=PAStatus.AWAITING_RECORDS,
            agent_name="patient_record",
            condition="docs_needed",
        ),
        Transition(
            next_status=PAStatus.FORM_FILLING,
            agent_name="pa_form_filling",
            condition="docs_complete",
        ),
    ],
    PAStatus.AWAITING_RECORDS: [
        Transition(
            next_status=PAStatus.DOCTOR_OUTREACH,
            agent_name="doctor_communication",
        ),
    ],
    PAStatus.DOCTOR_OUTREACH: [
        Transition(
            next_status=PAStatus.FOLLOWUP_PENDING,
            agent_name="followup",
            condition="awaiting_response",
        ),
        Transition(
            next_status=PAStatus.FORM_FILLING,
            agent_name="pa_form_filling",
            condition="docs_received",
        ),
    ],
    PAStatus.FOLLOWUP_PENDING: [
        Transition(
            next_status=PAStatus.FORM_FILLING,
            agent_name="pa_form_filling",
            condition="docs_received",
        ),
        Transition(
            next_status=PAStatus.DOCTOR_OUTREACH,
            agent_name="doctor_communication",
            condition="escalate",
        ),
    ],
    PAStatus.FORM_FILLING: [
        Transition(
            next_status=PAStatus.CLINICAL_WRITING,
            agent_name="clinical_writing",
        ),
    ],
    PAStatus.CLINICAL_WRITING: [
        Transition(
            next_status=PAStatus.READY_TO_SUBMIT,
            agent_name=None,
        ),
    ],
    PAStatus.READY_TO_SUBMIT: [
        Transition(
            next_status=PAStatus.SUBMITTED,
            agent_name="submission",
        ),
    ],
    PAStatus.SUBMITTED: [
        Transition(
            next_status=PAStatus.PENDING_REVIEW,
            agent_name="status_monitoring",
        ),
    ],
    PAStatus.PENDING_REVIEW: [
        Transition(
            next_status=PAStatus.APPROVED,
            agent_name="approval",
            condition="approved",
        ),
        Transition(
            next_status=PAStatus.DENIED,
            agent_name="denial_analysis",
            condition="denied",
        ),
        Transition(
            next_status=PAStatus.PENDING_REVIEW,
            agent_name="status_monitoring",
            condition="pending",
        ),
    ],
    PAStatus.APPROVED: [
        Transition(
            next_status=PAStatus.COMPLETED,
            agent_name="patient_communication",
        ),
    ],
    PAStatus.DENIED: [
        Transition(
            next_status=PAStatus.APPEAL_IN_PROGRESS,
            agent_name="appeal",
            condition="appealable",
        ),
        Transition(
            next_status=PAStatus.COMPLETED,
            agent_name="patient_communication",
            condition="final",
        ),
    ],
    PAStatus.APPEAL_IN_PROGRESS: [
        Transition(
            next_status=PAStatus.APPEAL_SUBMITTED,
            agent_name="submission",
        ),
    ],
    PAStatus.APPEAL_SUBMITTED: [
        Transition(
            next_status=PAStatus.APPEAL_APPROVED,
            agent_name="approval",
            condition="approved",
        ),
        Transition(
            next_status=PAStatus.APPEAL_DENIED,
            agent_name="patient_communication",
            condition="denied",
        ),
    ],
    PAStatus.APPEAL_APPROVED: [
        Transition(
            next_status=PAStatus.COMPLETED,
            agent_name="patient_communication",
        ),
    ],
    PAStatus.APPEAL_DENIED: [
        Transition(
            next_status=PAStatus.COMPLETED,
            agent_name="patient_communication",
        ),
    ],
}


class Orchestrator:
    """
    Coordinates the PA workflow state machine.
    Routes work to appropriate agents based on current state and conditions.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self._agent_registry: dict[str, BaseAgent] = {}
        self._build_registry()

    def _build_registry(self):
        from app.agents.prescription_intake import PrescriptionIntakeAgent
        from app.agents.pa_detection import PADetectionAgent
        from app.agents.insurance_verification import InsuranceVerificationAgent
        from app.agents.clinical_requirement import ClinicalRequirementAgent
        from app.agents.patient_record import PatientRecordAgent
        from app.agents.doctor_communication import DoctorCommunicationAgent
        from app.agents.followup import FollowupAgent
        from app.agents.pa_form_filling import PAFormFillingAgent
        from app.agents.clinical_writing import ClinicalWritingAgent
        from app.agents.submission import SubmissionAgent
        from app.agents.status_monitoring import StatusMonitoringAgent
        from app.agents.approval import ApprovalAgent
        from app.agents.denial_analysis import DenialAnalysisAgent
        from app.agents.appeal import AppealAgent
        from app.agents.patient_communication import PatientCommunicationAgent
        from app.agents.revenue_analytics import RevenueAnalyticsAgent

        agents = [
            PrescriptionIntakeAgent(self.db),
            PADetectionAgent(self.db),
            InsuranceVerificationAgent(self.db),
            ClinicalRequirementAgent(self.db),
            PatientRecordAgent(self.db),
            DoctorCommunicationAgent(self.db),
            FollowupAgent(self.db),
            PAFormFillingAgent(self.db),
            ClinicalWritingAgent(self.db),
            SubmissionAgent(self.db),
            StatusMonitoringAgent(self.db),
            ApprovalAgent(self.db),
            DenialAnalysisAgent(self.db),
            AppealAgent(self.db),
            PatientCommunicationAgent(self.db),
            RevenueAnalyticsAgent(self.db),
        ]
        self._agent_registry = {a.agent_name: a for a in agents}

    def get_agent(self, name: str) -> BaseAgent | None:
        return self._agent_registry.get(name)

    async def create_pa(self, prescription_id: str, patient_id: str, insurance_id: str | None = None) -> str:
        """Create the PA row in INTAKE and return its id. Does not run any agent."""
        import uuid

        pa = PriorAuth(
            id=str(uuid.uuid4()),
            patient_id=patient_id,
            prescription_id=prescription_id,
            insurance_id=insurance_id,
            status=PAStatus.INTAKE.value,
            current_agent="prescription_intake",
        )
        self.db.add(pa)
        await self.db.commit()
        await self.db.refresh(pa)

        logger.info("workflow.pa_created", prior_auth_id=pa.id, prescription_id=prescription_id)
        return pa.id

    async def run_intake(self, prior_auth_id: str) -> AgentResult:
        """Run the intake agent on an existing PA and auto-advance from INTAKE."""
        pa = await self.db.get(PriorAuth, prior_auth_id)
        if not pa:
            return AgentResult(success=False, error="PA not found")

        context = AgentContext(
            prior_auth_id=pa.id,
            patient_id=pa.patient_id,
            prescription_id=pa.prescription_id,
            insurance_id=pa.insurance_id,
        )
        intake_agent = self._agent_registry["prescription_intake"]
        result = await intake_agent.run(context)

        if result.success:
            await self.advance(pa.id, condition=result.condition)

        return result

    async def start_workflow(self, prescription_id: str, patient_id: str, insurance_id: str | None = None) -> str:
        """
        Entry point: creates a PA case and runs the intake agent inline.
        Returns the prior_auth_id. For out-of-band execution, use create_pa()
        and dispatch run_pa_workflow instead.
        """
        pa_id = await self.create_pa(prescription_id, patient_id, insurance_id)
        logger.info("workflow.started", prior_auth_id=pa_id, prescription_id=prescription_id)
        await self.run_intake(pa_id)
        return pa_id

    # Ceiling on chained auto-advances per external trigger. Prevents unbounded
    # Claude spend from self-transitions (e.g. PENDING_REVIEW -> pending -> ...).
    MAX_ADVANCE_DEPTH = 8

    async def advance(
        self,
        prior_auth_id: str,
        condition: str | None = None,
        _depth: int = 0,
    ) -> AgentResult | None:
        """
        Advance a PA case through the workflow.
        Finds the matching transition, updates state, runs the next agent.
        """
        if _depth >= self.MAX_ADVANCE_DEPTH:
            logger.warning(
                "workflow.max_depth_reached",
                prior_auth_id=prior_auth_id,
                depth=_depth,
            )
            return AgentResult(
                success=True,
                message="Workflow paused: max auto-advance depth reached",
            )
        pa = await self.db.get(PriorAuth, prior_auth_id)
        if not pa:
            logger.error("workflow.pa_not_found", prior_auth_id=prior_auth_id)
            return None

        current_status = PAStatus(pa.status)
        transitions = WORKFLOW_TRANSITIONS.get(current_status, [])

        if not transitions:
            logger.info("workflow.no_transitions", status=current_status, prior_auth_id=prior_auth_id)
            return None

        # Find matching transition
        transition = self._match_transition(transitions, condition)
        if not transition:
            logger.warning(
                "workflow.no_matching_transition",
                status=current_status,
                condition=condition,
                prior_auth_id=prior_auth_id,
            )
            return None

        # Update PA state
        pa.status = transition.next_status.value
        pa.current_agent = transition.agent_name
        await self.db.commit()

        logger.info(
            "workflow.transition",
            prior_auth_id=prior_auth_id,
            from_status=current_status.value,
            to_status=transition.next_status.value,
            agent=transition.agent_name,
            condition=condition,
        )

        # Run the agent if one is specified
        if transition.agent_name:
            agent = self._agent_registry.get(transition.agent_name)
            if not agent:
                logger.error("workflow.agent_not_found", agent_name=transition.agent_name)
                return AgentResult(success=False, error=f"Agent {transition.agent_name} not found")

            context = AgentContext(
                prior_auth_id=pa.id,
                patient_id=pa.patient_id,
                prescription_id=pa.prescription_id,
                insurance_id=pa.insurance_id,
            )
            result = await agent.run(context)

            # Auto-advance if agent completed successfully and provides a condition
            if result.success and not result.requires_human:
                if result.condition:
                    await self.advance(prior_auth_id, condition=result.condition, _depth=_depth + 1)
                elif result.next_agent:
                    # Agent explicitly requested next step
                    next_transitions = WORKFLOW_TRANSITIONS.get(PAStatus(pa.status), [])
                    if next_transitions and len(next_transitions) == 1:
                        await self.advance(prior_auth_id, _depth=_depth + 1)

            return result

        # No agent to run (terminal or pass-through state)
        # Check if we should auto-advance further
        next_transitions = WORKFLOW_TRANSITIONS.get(transition.next_status, [])
        if next_transitions and len(next_transitions) == 1 and next_transitions[0].condition is None:
            await self.advance(prior_auth_id, _depth=_depth + 1)

        return AgentResult(success=True, message=f"Transitioned to {transition.next_status.value}")

    async def trigger_agent(self, prior_auth_id: str, agent_name: str, force: bool = False) -> AgentResult:
        """Manually trigger a specific agent on a PA case."""
        pa = await self.db.get(PriorAuth, prior_auth_id)
        if not pa:
            return AgentResult(success=False, error="PA not found")

        agent = self._agent_registry.get(agent_name)
        if not agent:
            return AgentResult(success=False, error=f"Agent {agent_name} not found")

        context = AgentContext(
            prior_auth_id=pa.id,
            patient_id=pa.patient_id,
            prescription_id=pa.prescription_id,
            insurance_id=pa.insurance_id,
        )

        pa.current_agent = agent_name
        await self.db.commit()

        return await agent.run(context)

    def _match_transition(self, transitions: list[Transition], condition: str | None) -> Transition | None:
        """Find the first transition matching the given condition."""
        # If condition provided, look for exact match
        if condition:
            for t in transitions:
                if t.condition == condition:
                    return t

        # If no condition, return the first unconditional transition
        for t in transitions:
            if t.condition is None:
                return t

        # Fallback: return first transition if only one exists
        if len(transitions) == 1:
            return transitions[0]

        return None
