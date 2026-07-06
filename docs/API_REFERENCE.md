# API Reference

Base URL: `http://localhost:8000/api/v1`

Interactive docs: `http://localhost:8000/docs` (Swagger UI)

---

## Health

### GET /health
Check system health.

**Response 200:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-01-15T10:30:00Z",
  "database": "connected",
  "redis": "connected"
}
```

### GET /health/ready
Check if the system is ready to accept traffic.

---

## Prescriptions

### POST /prescriptions/intake
Intake a new prescription and automatically start the PA workflow.

**Request (multipart/form-data):**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| patient_id | string | Yes | Patient UUID |
| prescriber_npi | string | Yes | 10-digit NPI |
| drug_name | string | Yes | Medication name |
| prescriber_name | string | No | Prescriber full name |
| prescriber_phone | string | No | Office phone |
| prescriber_fax | string | No | Office fax |
| strength | string | No | Drug strength |
| quantity | int | No | Quantity to dispense |
| days_supply | int | No | Days supply |
| directions | string | No | Sig |
| ndc | string | No | 11-digit NDC |
| insurance_id | string | No | Insurance plan UUID |
| image | file | No | Prescription image for OCR |

**Response 200:**
```json
{
  "prescription_id": "uuid-here",
  "prior_auth_id": "uuid-here",
  "status": "workflow_started",
  "message": "Prescription intake complete. PA workflow initiated for Ozempic."
}
```

### POST /prescriptions
Create a prescription record without triggering the workflow.

### GET /prescriptions
List prescriptions. Query params: `skip`, `limit`, `status`, `patient_id`

### GET /prescriptions/{id}
Get a single prescription.

---

## Prior Authorizations

### POST /prior-auths
Manually create a PA case.

**Request:**
```json
{
  "patient_id": "uuid",
  "prescription_id": "uuid",
  "insurance_id": "uuid",
  "priority": 5,
  "notes": "Urgent - patient running out"
}
```

### GET /prior-auths
List PA cases. Query params: `skip`, `limit`, `status`, `patient_id`, `escalated`

**Response 200:**
```json
[
  {
    "id": "uuid",
    "patient_id": "uuid",
    "prescription_id": "uuid",
    "status": "pending_review",
    "decision": null,
    "pa_number": "PA-2024-001234",
    "submitted_at": "2024-01-15T10:30:00Z",
    "current_agent": "status_monitoring",
    "escalated": false,
    "priority": 5,
    "created_at": "2024-01-14T08:00:00Z"
  }
]
```

### GET /prior-auths/{id}
Get full PA detail.

### PUT /prior-auths/{id}
Update a PA case (manual override).

### GET /prior-auths/{id}/timeline
Get the complete execution history (every agent that ran, with timing and data).

**Response 200:**
```json
{
  "prior_auth_id": "uuid",
  "current_status": "pending_review",
  "events": [
    {
      "timestamp": "2024-01-14T08:00:00Z",
      "agent_name": "prescription_intake",
      "action": "prescription_intake execution",
      "status": "completed",
      "duration_ms": 2340,
      "details": {"drug_name": "Ozempic", "confidence": 0.95}
    },
    {
      "timestamp": "2024-01-14T08:00:03Z",
      "agent_name": "pa_detection",
      "action": "pa_detection execution",
      "status": "completed",
      "duration_ms": 1890,
      "details": {"pa_required": true, "reason": "Non-preferred specialty drug"}
    }
  ],
  "total_duration_hours": 26.5
}
```

### POST /prior-auths/{id}/trigger/{agent_name}
Manually trigger a specific agent. Query param: `force` (bool).

**Example:** `POST /prior-auths/abc123/trigger/clinical_writing`

**Response 200:**
```json
{
  "success": true,
  "agent": "clinical_writing",
  "message": "Medical necessity letter generated. Strength: strong.",
  "data": {"letter_text": "...", "estimated_strength": "strong"},
  "requires_human": false
}
```

### POST /prior-auths/{id}/advance
Manually advance the workflow. Query param: `condition` (e.g., "approved", "denied").

### POST /prior-auths/{id}/cancel
Cancel a PA case.

### POST /prior-auths/{id}/escalate
Escalate to human review. Query param: `assigned_to` (staff name).

---

## Patients

### POST /patients
Create a patient.

**Request:**
```json
{
  "first_name": "John",
  "last_name": "Smith",
  "date_of_birth": "1965-03-15",
  "phone": "5551234567",
  "email": "john@email.com",
  "member_id": "MBR001234",
  "group_number": "GRP001",
  "insurance_id": "uuid"
}
```

### GET /patients
List patients. Query params: `skip`, `limit`, `search` (searches name/member_id).

### GET /patients/{id}
Get patient details.

### PUT /patients/{id}
Update patient.

### GET /patients/{id}/prior-auths
Get all PA cases for a patient.

---

## Insurance

### POST /insurance/verify
Run real-time eligibility verification.

**Request:**
```json
{
  "member_id": "MBR001234",
  "bin_number": "003585",
  "pcn": "MEDDADV",
  "group_number": "GRP001",
  "patient_dob": "1965-03-15"
}
```

**Response 200:**
```json
{
  "is_active": true,
  "plan_name": "BCBS PPO",
  "coverage_type": "commercial",
  "copay": 35.0,
  "deductible_remaining": 500.0,
  "step_therapy_required": true,
  "quantity_limit_applies": false
}
```

### GET /insurance/plans
List cached insurance plans.

### POST /insurance/plans
Create an insurance plan record.

---

## Communications

### GET /communications
List all communications. Query params: `prior_auth_id`, `channel`, `status`.

### GET /communications/{id}
Get a single communication.

### POST /communications/{id}/resend
Resend a failed communication.

---

## Appeals

### POST /appeals
Initiate an appeal (triggers the appeal agent).

**Request:**
```json
{
  "prior_auth_id": "uuid",
  "level": 1,
  "denial_reason": "Step therapy not completed",
  "denial_codes": {"code": "75", "category": "STEP_THERAPY"}
}
```

### GET /appeals
List appeals. Query params: `prior_auth_id`, `status`.

### GET /appeals/{id}
Get appeal details including the generated letter.

---

## Analytics

### GET /analytics/dashboard
Get summary dashboard metrics.

**Response 200:**
```json
{
  "total_pas": 156,
  "pending_pas": 23,
  "approved_today": 8,
  "denied_today": 2,
  "average_turnaround_hours": 48.5,
  "approval_rate": 78.5,
  "appeal_success_rate": 62.0,
  "revenue_recovered_mtd": 125000.00,
  "top_rejected_drugs": [
    {"drug": "Ozempic", "count": 12},
    {"drug": "Humira", "count": 8}
  ]
}
```

### GET /analytics/revenue
Revenue recovery metrics.

### GET /analytics/turnaround
PA turnaround time metrics.

### GET /analytics/agent-performance
Per-agent performance metrics (success rate, duration, token usage).

---

## Documents

### POST /documents/upload
Upload a clinical document (multipart/form-data).

**Fields:** `prior_auth_id`, `document_type`, `file` (the file).

### GET /documents
List documents. Query params: `prior_auth_id`, `document_type`.

### GET /documents/{id}/download
Download/retrieve a document.

---

## Agents

### GET /agents/types
List all 16 agent types with descriptions.

### GET /agents/executions
List agent execution history. Query params: `agent_name`, `prior_auth_id`, `status`.

### GET /agents/stats
Aggregate agent statistics (runs, duration, tokens).

---

## Webhooks (Inbound)

### POST /webhooks/covermymeds
CoverMyMeds status update callback.

### POST /webhooks/epa
ePA (NCPDP SCRIPT) status callback.

### POST /webhooks/fax
Fax delivery receipt callback.

---

## Error Responses

All errors follow this format:
```json
{
  "detail": "Human-readable error message"
}
```

| Status Code | Meaning |
|-------------|---------|
| 400 | Bad request (validation error) |
| 401 | Not authenticated |
| 403 | Not authorized |
| 404 | Resource not found |
| 422 | Validation error (Pydantic) |
| 500 | Internal server error |
