from pydantic import BaseModel
from datetime import datetime


class AppealCreate(BaseModel):
    prior_auth_id: str
    level: int = 1
    denial_reason: str | None = None
    denial_codes: dict | None = None


class AppealRead(BaseModel):
    id: str
    prior_auth_id: str
    appeal_number: str | None = None
    level: int
    status: str
    denial_reason: str | None = None
    appeal_strategy: str | None = None
    appeal_letter: str | None = None
    supporting_evidence: dict | None = None
    clinical_references: dict | None = None
    submitted_at: datetime | None = None
    decision_at: datetime | None = None
    decision: str | None = None
    decision_notes: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class DenialAnalysis(BaseModel):
    prior_auth_id: str
    denial_reason: str
    denial_category: str
    missing_items: list[str] = []
    root_cause: str
    is_appealable: bool
    appeal_success_probability: float | None = None
    recommended_strategy: str
    additional_evidence_needed: list[str] = []
    suggested_alternatives: list[str] = []
