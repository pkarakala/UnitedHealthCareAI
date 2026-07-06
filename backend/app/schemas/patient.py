from pydantic import BaseModel, EmailStr
from datetime import date, datetime


class PatientBase(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: date
    phone: str | None = None
    email: str | None = None
    address: dict | None = None
    member_id: str | None = None
    group_number: str | None = None
    insurance_id: str | None = None


class PatientCreate(PatientBase):
    pass


class PatientUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    email: str | None = None
    address: dict | None = None
    member_id: str | None = None
    group_number: str | None = None
    insurance_id: str | None = None


class PatientRead(PatientBase):
    id: str
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}
