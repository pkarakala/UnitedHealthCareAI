import uuid
from datetime import date

import pytest
from app.utils.constants import PAStatus
from app.agents.base import AgentResult
from app.agents.orchestrator import Orchestrator, WORKFLOW_TRANSITIONS, Transition
from app.models.patient import Patient
from app.models.prescription import Prescription
from app.models.prior_auth import PriorAuth


def test_workflow_transitions_complete():
    """Verify all non-terminal states have at least one transition."""
    terminal_states = {PAStatus.COMPLETED, PAStatus.CANCELLED, PAStatus.ERROR}
    for status in PAStatus:
        if status not in terminal_states:
            assert status in WORKFLOW_TRANSITIONS, f"Missing transitions for {status}"


def test_pa_detection_branches():
    """PA Detection should have both pa_required and not_required paths."""
    transitions = WORKFLOW_TRANSITIONS[PAStatus.PA_DETECTION]
    conditions = [t.condition for t in transitions]
    assert "pa_required" in conditions
    assert "not_required" in conditions


def test_pending_review_branches():
    """Pending Review should handle approved, denied, and pending."""
    transitions = WORKFLOW_TRANSITIONS[PAStatus.PENDING_REVIEW]
    conditions = [t.condition for t in transitions]
    assert "approved" in conditions
    assert "denied" in conditions
    assert "pending" in conditions


def test_denied_branches():
    """Denied should have appealable and final paths."""
    transitions = WORKFLOW_TRANSITIONS[PAStatus.DENIED]
    conditions = [t.condition for t in transitions]
    assert "appealable" in conditions
    assert "final" in conditions


def test_transition_agents_exist():
    """All agent names referenced in transitions should be valid."""
    valid_agents = {
        "prescription_intake", "pa_detection", "insurance_verification",
        "clinical_requirement", "patient_record", "doctor_communication",
        "followup", "pa_form_filling", "clinical_writing", "submission",
        "status_monitoring", "approval", "denial_analysis", "appeal",
        "patient_communication", "revenue_analytics",
    }
    for status, transitions in WORKFLOW_TRANSITIONS.items():
        for t in transitions:
            if t.agent_name:
                assert t.agent_name in valid_agents, (
                    f"Invalid agent '{t.agent_name}' in transition from {status}"
                )


class _StubAgent:
    """Minimal stand-in for a workflow agent with a canned run() result."""

    def __init__(self, agent_name, result):
        self.agent_name = agent_name
        self._result = result
        self.ran = False

    async def run(self, context):
        self.ran = True
        return self._result


async def _seed_pa(db, status: PAStatus) -> PriorAuth:
    patient = Patient(
        id=str(uuid.uuid4()), first_name="T", last_name="X",
        date_of_birth=date(1990, 1, 1),
    )
    rx = Prescription(
        id=str(uuid.uuid4()), patient_id=patient.id,
        prescriber_npi="1234567890", drug_name="Ozempic",
    )
    pa = PriorAuth(
        id=str(uuid.uuid4()), patient_id=patient.id, prescription_id=rx.id,
        status=status.value,
    )
    db.add_all([patient, rx, pa])
    await db.commit()
    return pa


@pytest.mark.asyncio
async def test_transition_held_when_agent_fails(db_session):
    # INTAKE -> PA_DETECTION runs the pa_detection agent.
    pa = await _seed_pa(db_session, PAStatus.INTAKE)
    orch = Orchestrator(db_session)
    orch._agent_registry["pa_detection"] = _StubAgent(
        "pa_detection", AgentResult(success=False, error="boom")
    )

    result = await orch.advance(pa.id)

    assert result.success is False
    await db_session.refresh(pa)
    # Status must NOT have advanced — the failed agent leaves it recoverable.
    assert pa.status == PAStatus.INTAKE.value


@pytest.mark.asyncio
async def test_transition_held_when_requires_human(db_session):
    pa = await _seed_pa(db_session, PAStatus.INTAKE)
    orch = Orchestrator(db_session)
    orch._agent_registry["pa_detection"] = _StubAgent(
        "pa_detection", AgentResult(success=True, requires_human=True)
    )

    await orch.advance(pa.id)

    await db_session.refresh(pa)
    assert pa.status == PAStatus.INTAKE.value


@pytest.mark.asyncio
async def test_transition_commits_on_success(db_session):
    pa = await _seed_pa(db_session, PAStatus.INTAKE)
    orch = Orchestrator(db_session)
    # Succeed with no condition so it doesn't cascade into further agents.
    orch._agent_registry["pa_detection"] = _StubAgent(
        "pa_detection", AgentResult(success=True)
    )

    await orch.advance(pa.id)

    await db_session.refresh(pa)
    assert pa.status == PAStatus.PA_DETECTION.value
    assert pa.lock_version == 1  # bumped exactly once


@pytest.mark.asyncio
async def test_successful_transition_bumps_lock_version(db_session):
    pa = await _seed_pa(db_session, PAStatus.INTAKE)
    orch = Orchestrator(db_session)
    from app.agents.orchestrator import Transition

    committed = await orch._commit_transition(
        pa,
        Transition(next_status=PAStatus.PA_DETECTION, agent_name="pa_detection"),
        PAStatus.INTAKE,
        condition=None,
        expected_version=0,
    )
    assert committed is True
    assert pa.lock_version == 1


@pytest.mark.asyncio
async def test_stale_version_rejects_transition(db_session):
    # Simulates a concurrent worker having already advanced the PA: the second
    # commit sees expected_version=0 but the row is now at version 1, so it must
    # not overwrite the state.
    pa = await _seed_pa(db_session, PAStatus.PA_DETECTION)
    pa.lock_version = 1
    await db_session.commit()

    orch = Orchestrator(db_session)
    from app.agents.orchestrator import Transition

    committed = await orch._commit_transition(
        pa,
        Transition(next_status=PAStatus.INSURANCE_VERIFICATION, agent_name="insurance_verification"),
        PAStatus.PA_DETECTION,
        condition="pa_required",
        expected_version=0,  # stale
    )

    assert committed is False
    await db_session.refresh(pa)
    assert pa.status == PAStatus.PA_DETECTION.value  # unchanged
    assert pa.lock_version == 1
