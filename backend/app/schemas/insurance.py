from pydantic import BaseModel
from datetime import datetime


class InsuranceBase(BaseModel):
    plan_name: str
    payer_name: str | None = None
    bin_number: str | None = None
    pcn: str | None = None
    group_number: str | None = None
    phone: str | None = None
    fax: str | None = None
    portal_url: str | None = None


class InsuranceCreate(InsuranceBase):
    formulary_data: dict | None = None
    pa_requirements: dict | None = None
    step_therapy_rules: dict | None = None
    quantity_limits: dict | None = None


class InsuranceRead(InsuranceBase):
    id: str
    is_active: bool
    formulary_data: dict | None = None
    pa_requirements: dict | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class InsuranceVerificationRequest(BaseModel):
    member_id: str
    bin_number: str | None = None
    pcn: str | None = None
    group_number: str | None = None
    patient_dob: str | None = None


class InsuranceVerificationResult(BaseModel):
    is_active: bool
    plan_name: str | None = None
    coverage_type: str | None = None
    copay: float | None = None
    deductible_remaining: float | None = None
    preferred_pharmacy: bool | None = None
    step_therapy_required: bool = False
    quantity_limit_applies: bool = False
    age_restriction: bool = False
    diagnosis_restriction: bool = False
    notes: str | None = None
