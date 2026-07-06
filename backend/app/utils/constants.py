from enum import Enum


class PAStatus(str, Enum):
    INTAKE = "intake"
    PA_DETECTION = "pa_detection"
    NO_PA_REQUIRED = "no_pa_required"
    INSURANCE_VERIFICATION = "insurance_verification"
    CLINICAL_REVIEW = "clinical_review"
    AWAITING_RECORDS = "awaiting_records"
    DOCTOR_OUTREACH = "doctor_outreach"
    FOLLOWUP_PENDING = "followup_pending"
    FORM_FILLING = "form_filling"
    CLINICAL_WRITING = "clinical_writing"
    READY_TO_SUBMIT = "ready_to_submit"
    SUBMITTED = "submitted"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    DENIED = "denied"
    APPEAL_IN_PROGRESS = "appeal_in_progress"
    APPEAL_SUBMITTED = "appeal_submitted"
    APPEAL_APPROVED = "appeal_approved"
    APPEAL_DENIED = "appeal_denied"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ERROR = "error"


class AgentType(str, Enum):
    PRESCRIPTION_INTAKE = "prescription_intake"
    PA_DETECTION = "pa_detection"
    INSURANCE_VERIFICATION = "insurance_verification"
    CLINICAL_REQUIREMENT = "clinical_requirement"
    PATIENT_RECORD = "patient_record"
    DOCTOR_COMMUNICATION = "doctor_communication"
    FOLLOWUP = "followup"
    PA_FORM_FILLING = "pa_form_filling"
    CLINICAL_WRITING = "clinical_writing"
    SUBMISSION = "submission"
    STATUS_MONITORING = "status_monitoring"
    APPROVAL = "approval"
    DENIAL_ANALYSIS = "denial_analysis"
    APPEAL = "appeal"
    PATIENT_COMMUNICATION = "patient_communication"
    REVENUE_ANALYTICS = "revenue_analytics"


class CommunicationChannel(str, Enum):
    FAX = "fax"
    EMAIL = "email"
    SMS = "sms"
    PHONE = "phone"
    PORTAL = "portal"


class CommunicationStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    READ = "read"


class DocumentType(str, Enum):
    PRESCRIPTION_IMAGE = "prescription_image"
    LAB_RESULT = "lab_result"
    CLINICAL_NOTE = "clinical_note"
    MEDICAL_NECESSITY_LETTER = "medical_necessity_letter"
    APPEAL_LETTER = "appeal_letter"
    DENIAL_LETTER = "denial_letter"
    INSURANCE_CARD = "insurance_card"
    PROGRESS_NOTE = "progress_note"


class SubmissionMethod(str, Enum):
    EPA = "epa"
    COVERMYMEDS = "covermymeds"
    FAX = "fax"
    PORTAL = "portal"
    PHONE = "phone"
