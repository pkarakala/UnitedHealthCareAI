from pydantic import BaseModel
from datetime import datetime


class AgentInput(BaseModel):
    prior_auth_id: str
    patient_id: str
    prescription_id: str
    insurance_id: str | None = None
    metadata: dict = {}


class AgentOutput(BaseModel):
    success: bool
    data: dict = {}
    next_agent: str | None = None
    error: str | None = None
    tokens_used: int = 0
    requires_human: bool = False
    message: str | None = None


class AgentExecutionRead(BaseModel):
    id: str
    prior_auth_id: str
    agent_name: str
    status: str
    started_at: datetime
    completed_at: datetime | None = None
    duration_ms: int | None = None
    tokens_input: int | None = None
    tokens_output: int | None = None
    model_used: str | None = None
    cost_usd: float | None = None
    error_message: str | None = None

    model_config = {"from_attributes": True}


class AgentTriggerRequest(BaseModel):
    agent_name: str
    force: bool = False
    metadata: dict = {}
