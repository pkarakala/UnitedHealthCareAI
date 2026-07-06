# Agents Guide

This document explains how each of the 16 AI agents works, what they do, and how they interact with the system.

## Agent Architecture

Every agent inherits from `BaseAgent` (defined in `backend/app/agents/base.py`):

```python
class BaseAgent(ABC):
    agent_name: str       # Unique identifier
    model: str            # Claude model to use
    max_tokens: int       # Max response tokens
    temperature: float    # Creativity (low = deterministic)

    # Methods every agent implements:
    async def execute(context) -> AgentResult     # Core logic
    def get_system_prompt() -> str                # Claude instructions

    # Methods provided by base class:
    async def run(context) -> AgentResult          # Lifecycle wrapper
    async def call_claude_text(msg) -> (str, int, int)
    async def call_claude_json(msg) -> (dict, int, int)
```

**AgentContext** carries the IDs needed to load data:
```python
class AgentContext:
    prior_auth_id: str
    patient_id: str
    prescription_id: str
    insurance_id: str | None
    metadata: dict
```

**AgentResult** is what every agent returns:
```python
class AgentResult:
    success: bool          # Did the agent complete successfully?
    data: dict             # Structured output data
    condition: str | None  # Routing hint for orchestrator
    next_agent: str | None # Explicit next step
    requires_human: bool   # Should we pause for human review?
    tokens_input: int      # Claude tokens consumed
    tokens_output: int     # Claude tokens generated
    message: str | None    # Human-readable summary
```

---

## Agent 1: Prescription Intake

**File:** `agents/prescription_intake.py`
**Purpose:** Read and extract data from prescriptions (electronic, fax, paper, phone)

**What it does:**
1. Loads the prescription record from the database
2. If an image is attached, uses Claude's vision to OCR it
3. Extracts: drug name, strength, quantity, directions, prescriber info, diagnosis codes
4. Validates extracted data for completeness
5. Updates the prescription record with verified data

**Input:** Raw prescription data (possibly incomplete)
**Output:** Structured, verified prescription data with confidence score

**When it might need a human:** If OCR confidence is very low or critical fields can't be read.

---

## Agent 2: PA Detection

**File:** `agents/pa_detection.py`
**Purpose:** Determine if prior authorization is required

**What it does:**
1. Checks the drug against the insurance formulary
2. Looks for NCPDP reject codes (75, 76)
3. Evaluates step therapy requirements
4. Checks quantity limits and age/diagnosis restrictions
5. Identifies preferred alternatives

**Input:** Prescription + Insurance data
**Output:** `pa_required: true/false` with reasoning

**Key decision point:** This agent splits the workflow — if PA isn't needed, the prescription goes straight to fill.

---

## Agent 3: Insurance Verification

**File:** `agents/insurance_verification.py`
**Purpose:** Verify patient eligibility and coverage details

**What it does:**
1. Validates Member ID, BIN, PCN, Group
2. Confirms coverage is active
3. Determines drug tier and copay
4. Identifies step therapy or quantity restrictions
5. Finds the correct submission method (ePA, CoverMyMeds, fax)

**Input:** Patient demographics + Insurance plan data
**Output:** Verification result with coverage details and restrictions

**Production integration:** Would call Change Healthcare or Availity eligibility APIs.

---

## Agent 4: Clinical Requirement

**File:** `agents/clinical_requirement.py`
**Purpose:** Identify what documentation the payer requires for approval

**What it does:**
1. Knows payer-specific PA requirements per drug
2. Example: Ozempic needs Type 2 diabetes, HbA1c > 7%, metformin failure
3. Compares required docs against what's already collected
4. Generates a checklist of missing items

**Input:** Drug name + Insurance plan + Available patient data
**Output:** Documentation checklist with missing items highlighted

**Key decision point:** If all docs are available, skip to form filling. Otherwise, proceed to record retrieval and doctor outreach.

---

## Agent 5: Patient Record Retrieval

**File:** `agents/patient_record.py`
**Purpose:** Compile clinical data from available sources

**What it does:**
1. Queries pharmacy management system for fill history
2. Retrieves diagnoses, allergies, lab values
3. Finds previous PA attempts and therapy failures
4. Identifies data gaps that require prescriber input

**Input:** Patient ID + Required documentation list
**Output:** Structured clinical profile with data gaps noted

**Production integration:** Would connect to pharmacy system APIs, EHR integrations, Health Information Exchanges (HIE).

---

## Agent 6: Doctor Communication

**File:** `agents/doctor_communication.py`
**Purpose:** Generate outreach to prescriber offices requesting documentation

**What it does:**
1. Creates a professional fax cover letter with checklist
2. Generates a concise email with clear asks
3. Writes a phone script for calling the office
4. Crafts a portal message for EHR communication
5. Saves all communications to the database

**Input:** Missing documentation list + Prescriber contact info
**Output:** Multi-channel communication templates ready to send

**Why this matters:** This is where pharmacies spend enormous staff time. Automating outreach generation saves hours per day.

---

## Agent 7: Follow-up

**File:** `agents/followup.py`
**Purpose:** Manage escalation timeline when prescriber hasn't responded

**Schedule:**
- Day 1: Gentle reminder (same channel as initial)
- Day 2: Phone call to office
- Day 4: Multi-channel reminder (fax + portal + phone)
- Day 6: Escalate to pharmacy manager

**What it does:**
1. Calculates days since initial outreach
2. Reviews communication history
3. Determines escalation level
4. Generates appropriate follow-up messages
5. Flags for human intervention when max attempts reached

**Triggered by:** Celery Beat schedule (every hour)

---

## Agent 8: PA Form Filling

**File:** `agents/pa_form_filling.py`
**Purpose:** Map patient/drug/clinical data to PA form fields

**What it does:**
1. Loads all collected patient, prescription, insurance, and clinical data
2. Maps each piece of data to the correct form field
3. Determines which submission platform to use
4. Identifies any fields that still can't be filled
5. Reports form completeness percentage

**Input:** All collected data for the PA case
**Output:** Complete form field mapping + submission method

**Why this matters:** Form filling typically takes 5-10 minutes per PA manually. This agent does it in seconds.

---

## Agent 9: Clinical Writing

**File:** `agents/clinical_writing.py`
**Purpose:** Generate medical necessity letters and clinical summaries

**What it does:**
1. Compiles all clinical evidence (diagnoses, labs, therapy failures)
2. Writes a persuasive medical necessity letter
3. Cites relevant clinical practice guidelines
4. Formats prior treatment history narrative
5. Estimates the strength of the clinical argument

**Input:** Clinical data + Drug requirements
**Output:** Complete medical necessity letter + clinical summary

**Quality indicators:** Letter strength rated as "strong", "moderate", or "weak" based on available evidence.

---

## Agent 10: Submission

**File:** `agents/submission.py`
**Purpose:** Submit the PA through the appropriate channel

**Channels:**
- **ePA**: Electronic PA via NCPDP SCRIPT (fastest: 24-72 hours)
- **CoverMyMeds**: Web platform (48-72 hours)
- **Insurance Portal**: Direct payer portal (72 hours - 2 weeks)
- **Fax**: Traditional fax (5-14 business days)

**What it does:**
1. Selects the best submission channel
2. Packages form data + medical necessity letter + supporting docs
3. Submits to the appropriate system
4. Records confirmation number and expected response time
5. Sets the PA status to "submitted"

**Production integration:** CoverMyMeds API, NCPDP SCRIPT transactions, fax APIs.

---

## Agent 11: Status Monitoring

**File:** `agents/status_monitoring.py`
**Purpose:** Periodically check PA decision status

**What it does:**
1. Queries the submission platform for current status
2. Interprets the response (pending, approved, denied, need more info)
3. Updates the PA record if a decision was made
4. Determines next check time if still pending

**Triggered by:** Celery Beat schedule (every 2 hours)

**Why this matters:** Without automation, staff must log into multiple portals manually to check status.

---

## Agent 12: Approval Processing

**File:** `agents/approval.py`
**Purpose:** Handle all downstream actions when a PA is approved

**What it does:**
1. Updates pharmacy management system
2. Prepares claim reversal and rebill with PA override
3. Calculates patient copay
4. Generates technician fill instructions
5. Creates patient notification
6. Records revenue recovered

**Output:** Complete processing plan for the pharmacy team

---

## Agent 13: Denial Analysis

**File:** `agents/denial_analysis.py`
**Purpose:** Analyze why a PA was denied and determine next steps

**Denial categories it identifies:**
- Missing documentation
- Step therapy not completed
- Diagnosis doesn't match indication
- Quantity exceeds plan limits
- Drug excluded from formulary
- Administrative errors

**What it does:**
1. Reads the denial reason and codes
2. Categorizes the denial
3. Determines if it's appealable
4. Estimates appeal success probability
5. Recommends specific strategy

---

## Agent 14: Appeal

**File:** `agents/appeal.py`
**Purpose:** Draft appeal letters with clinical evidence

**What it does:**
1. Addresses the specific denial reason point-by-point
2. Cites clinical practice guidelines (ADA, ACR, NCCN, etc.)
3. References peer-reviewed literature
4. Includes new/additional evidence
5. Formats as a formal appeal letter
6. Provides peer-to-peer talking points if P2P review requested

**Input:** Denial analysis + All clinical data
**Output:** Complete appeal letter ready for submission

---

## Agent 15: Patient Communication

**File:** `agents/patient_communication.py`
**Purpose:** Keep patients informed via SMS, email, or phone

**Message types:**
- "Your prior authorization was approved."
- "We are waiting for your doctor's office to respond."
- "Your medication is ready for pickup."
- "We're appealing the denial — here's what's happening."

**HIPAA note:** SMS messages don't include specific drug names (they're too short to be secure). Email and phone provide more detail.

---

## Agent 16: Revenue Analytics

**File:** `agents/revenue_analytics.py`
**Purpose:** Compute business intelligence metrics

**Metrics tracked:**
- Average approval turnaround time (by insurance, by drug)
- Total revenue recovered (approved PAs * claim amounts)
- Top rejected drugs
- Top slow prescribers (response time)
- Top slow insurance companies (decision time)
- PA completion rate
- Appeal success rate
- Cost per PA (time + AI tokens)

**Output:** Dashboard-ready metrics for pharmacy owners

---

## Adding a New Agent

To add a new agent:

1. Create `agents/my_new_agent.py`
2. Inherit from `BaseAgent`
3. Set `agent_name = "my_new_agent"`
4. Implement `execute()` and `get_system_prompt()`
5. Register it in `orchestrator.py` `_build_registry()`
6. Add transitions in `WORKFLOW_TRANSITIONS` if it's part of the main flow
7. Add the agent name to `utils/constants.py` `AgentType` enum
