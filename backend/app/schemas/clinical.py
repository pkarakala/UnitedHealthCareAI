from pydantic import BaseModel


class ClinicalRequirement(BaseModel):
    drug_name: str
    payer_name: str
    required_diagnoses: list[str] = []
    required_labs: list[str] = []
    required_prior_therapies: list[str] = []
    step_therapy_drugs: list[str] = []
    documentation_needed: list[str] = []
    missing_items: list[str] = []
    notes: str | None = None


class MedicalNecessityLetter(BaseModel):
    patient_name: str
    drug_name: str
    diagnosis: str
    clinical_rationale: str
    prior_treatments: list[str] = []
    lab_results: list[dict] = []
    supporting_guidelines: list[str] = []
    letter_text: str
    confidence_score: float | None = None


class PatientClinicalRecord(BaseModel):
    patient_id: str
    medications_current: list[dict] = []
    medications_history: list[dict] = []
    allergies: list[str] = []
    diagnoses: list[dict] = []
    lab_results: list[dict] = []
    previous_pa_attempts: list[dict] = []
    fill_history: list[dict] = []
    progress_notes: list[str] = []
