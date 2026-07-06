from pydantic import BaseModel
from datetime import date, datetime


class PrescriptionBase(BaseModel):
    patient_id: str
    prescriber_npi: str
    prescriber_name: str | None = None
    prescriber_phone: str | None = None
    prescriber_fax: str | None = None
    drug_name: str
    ndc: str | None = None
    strength: str | None = None
    quantity: int | None = None
    days_supply: int | None = None
    refills: int | None = None
    directions: str | None = None
    diagnosis_codes: list[str] | None = None
    pharmacy_npi: str | None = None
    date_written: date | None = None
    source: str | None = None


class PrescriptionCreate(PrescriptionBase):
    pass


class PrescriptionRead(PrescriptionBase):
    id: str
    raw_image_url: str | None = None
    ocr_confidence: float | None = None
    status: str
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class OCRResult(BaseModel):
    drug_name: str
    strength: str | None = None
    quantity: int | None = None
    directions: str | None = None
    prescriber_name: str | None = None
    prescriber_npi: str | None = None
    patient_name: str | None = None
    date_written: str | None = None
    ndc: str | None = None
    diagnosis_codes: list[str] | None = None
    confidence: float
    raw_text: str
