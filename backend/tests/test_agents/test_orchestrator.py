import pytest
from app.utils.constants import PAStatus
from app.agents.orchestrator import Orchestrator, WORKFLOW_TRANSITIONS, Transition


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
