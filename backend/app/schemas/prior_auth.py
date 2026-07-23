from pydantic import BaseModel
from datetime import datetime
from app.utils.constants import PAStatus


class PriorAuthCreate(BaseModel):
    patient_id: str
    prescription_id: str
    insurance_id: str | None = None
    priority: int = 5
    notes: str | None = None


class PriorAuthUpdate(BaseModel):
    """
    Human-editable PA fields via PUT /prior-auths/{id}.

    Deliberately excludes status/sub_status/decision/denial_reason/pa_number/
    submission_method: those are driven by the workflow state machine
    (orchestrator, webhooks, agents), and letting a raw PUT set them would
    bypass the state machine and its concurrency guards. Use /advance,
    /cancel, /escalate, or the webhook endpoints to change PA state.
    """
    notes: str | None = None
    assigned_to: str | None = None
    priority: int | None = None

    model_config = {"extra": "forbid"}


class PriorAuthRead(BaseModel):
    id: str
    patient_id: str
    prescription_id: str
    insurance_id: str | None = None
    status: str
    sub_status: str | None = None
    pa_number: str | None = None
    confirmation_number: str | None = None
    submission_method: str | None = None
    submitted_at: datetime | None = None
    decision_at: datetime | None = None
    decision: str | None = None
    denial_reason: str | None = None
    medical_necessity_letter: str | None = None
    clinical_summary: str | None = None
    required_documents: dict | list | None = None
    collected_documents: dict | list | None = None
    claim_amount: float | None = None
    revenue_recovered: float | None = None
    current_agent: str | None = None
    is_simulated: bool = False
    simulated_agents: list | None = None
    retry_count: int
    escalated: bool
    assigned_to: str | None = None
    priority: int
    notes: str | None = None
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class TimelineEvent(BaseModel):
    timestamp: datetime
    agent_name: str | None = None
    action: str
    status: str
    details: dict | None = None
    duration_ms: int | None = None


class PriorAuthTimeline(BaseModel):
    prior_auth_id: str
    current_status: str
    events: list[TimelineEvent]
    total_duration_hours: float | None = None
