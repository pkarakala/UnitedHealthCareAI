# PA Workflow: How It Works

This document explains the prior authorization workflow in plain language. No programming knowledge required.

## What is Prior Authorization?

Prior authorization (PA) is when an insurance company requires approval before they'll pay for a medication. The pharmacy must prove the drug is medically necessary by submitting clinical documentation.

**The problem:** This process is mostly manual. Staff spend hours on the phone, faxing, filling forms, and checking portals. A single PA can take days.

**The solution:** This platform automates the entire process using AI agents that work 24/7.

---

## The Workflow (Step by Step)

### Step 1: A Prescription Arrives

A new prescription comes in — electronically, by fax, or on paper.

**What the AI does:**
- Reads the prescription (OCR if it's a scan)
- Extracts the drug name, dose, prescriber, patient info
- Stores everything in the system

**Time saved:** 2-3 minutes per prescription

---

### Step 2: Does This Need Prior Authorization?

Not every prescription needs a PA. The AI checks automatically.

**What the AI checks:**
- Is this drug on the insurance formulary?
- Does it require step therapy (trying cheaper drugs first)?
- Are there quantity limits?
- Did the claim get rejected with a PA-required code?

**If no PA needed:** Prescription goes straight to fill. Done!
**If PA needed:** Continue to next step.

---

### Step 3: Verify the Insurance

Before starting the PA, confirm the patient's insurance is active.

**What the AI checks:**
- Is the member ID valid?
- Is coverage active?
- What are the plan's specific PA requirements?
- Which portal should we submit through?

---

### Step 4: What Documentation is Needed?

Every insurance plan has specific requirements. The AI knows them.

**Example — Ozempic (for diabetes):**
- Diagnosis of Type 2 Diabetes (ICD-10 code)
- HbA1c lab result > 7%
- Failed metformin for at least 3 months
- Clinical notes

**The AI creates a checklist** of everything needed and identifies what's missing.

---

### Step 5: Gather Patient Records

The AI pulls together everything available from pharmacy records:
- Medication fill history
- Allergies
- Previous PA attempts
- Available lab results
- Diagnosis codes

---

### Step 6: Contact the Doctor's Office

This is where pharmacies spend the MOST time. The AI generates:

- **Fax:** Professional cover letter with a checklist the office can fill out and fax back
- **Email:** Concise request with clear deadline
- **Phone script:** Talking points if staff need to call
- **Portal message:** For EHR systems

**Time saved:** 10-15 minutes per PA (just for outreach creation)

---

### Step 7: Follow Up Automatically

If the doctor's office doesn't respond:

| Day | Action |
|-----|--------|
| Day 1 | Send a reminder |
| Day 2 | Call the office |
| Day 4 | Send reminders on all channels |
| Day 6 | Escalate to pharmacy manager |

**No human needed** unless escalation triggers.

---

### Step 8: Fill Out the PA Form

Once documentation is collected, the AI fills out the actual PA form:
- Patient demographics
- Prescriber information
- Drug details
- Clinical information
- Supporting documentation

**Time saved:** 5-10 minutes per PA

---

### Step 9: Write the Medical Necessity Letter

The AI writes a compelling clinical letter explaining why the drug is needed:
- States the diagnosis
- Lists failed prior medications
- Includes lab values
- Cites clinical guidelines
- Makes the case for approval

**This is where AI really shines.** Writing these letters manually takes 10-20 minutes and requires clinical knowledge.

---

### Step 10: Submit

The AI submits through the best available channel:
- **ePA** (electronic): Fastest — decision in 24-72 hours
- **CoverMyMeds**: Good tracking — 48-72 hours
- **Insurance portal**: Direct submission — 3-14 days
- **Fax**: Slowest — 5-14 business days

Records the confirmation number and expected response date.

---

### Step 11: Monitor for Decision

Instead of staff checking portals manually, the AI checks every 2 hours:
- Still pending?
- Approved?
- Denied?
- Need more info?

---

### Step 12: If APPROVED

The AI automatically:
1. Updates the pharmacy system
2. Reverses the rejected claim
3. Rebills with the PA approval code
4. Generates fill instructions for the technician
5. Notifies the patient: "Your medication is ready!"
6. Records the revenue recovered

---

### Step 13: If DENIED

The AI doesn't give up. It:
1. Reads the denial reason
2. Identifies what went wrong (missing labs? wrong diagnosis? step therapy?)
3. Determines if it can be appealed
4. Calculates probability of successful appeal
5. Recommends a strategy

---

### Step 14: Appeal

If the denial is appealable, the AI:
1. Drafts a formal appeal letter
2. Addresses the specific denial reason
3. Adds new clinical evidence
4. Cites medical guidelines and research
5. Submits the appeal

---

### Step 15: Notify the Patient

Throughout the process, patients receive updates:
- "We're working on your prior authorization."
- "We're waiting to hear from your doctor's office."
- "Great news — your medication was approved!"
- "We're appealing the decision. Here's what's happening."

---

### Step 16: Track Everything (Analytics)

The dashboard shows pharmacy owners:
- **Approval rate:** What percentage get approved
- **Turnaround time:** How long PAs take
- **Revenue recovered:** Money from approved PAs
- **Top rejected drugs:** Which drugs get denied most
- **Slow prescribers:** Which offices respond slowly
- **Slow insurers:** Which companies take longest

---

## Status Flow Diagram

```
INTAKE → PA_DETECTION → INSURANCE_VERIFICATION → CLINICAL_REVIEW
                                                       │
                                              ┌────────┴────────┐
                                              ▼                 ▼
                                        AWAITING_RECORDS    FORM_FILLING
                                              │                 ▲
                                              ▼                 │
                                        DOCTOR_OUTREACH ────────┘
                                              │
                                        FOLLOWUP_PENDING
                                              │
                                        FORM_FILLING → CLINICAL_WRITING → SUBMITTED
                                                                              │
                                                                        PENDING_REVIEW
                                                                         │         │
                                                                    APPROVED    DENIED
                                                                         │         │
                                                                    COMPLETED  APPEAL
                                                                              │
                                                                        APPEAL_SUBMITTED
                                                                         │         │
                                                                    APPROVED    DENIED
                                                                         │         │
                                                                    COMPLETED  COMPLETED
```

---

## How Much Time Does This Save?

| Task | Manual Time | AI Time | Savings |
|------|-------------|---------|---------|
| Prescription intake | 3 min | 5 sec | 2.9 min |
| PA detection | 2 min | 3 sec | 1.9 min |
| Insurance verification | 5 min | 10 sec | 4.8 min |
| Doctor outreach | 15 min | 10 sec | 14.8 min |
| Form filling | 10 min | 8 sec | 9.9 min |
| Medical necessity letter | 15 min | 15 sec | 14.8 min |
| Submission | 5 min | 5 sec | 4.9 min |
| Status checking (per check) | 3 min | 5 sec | 2.9 min |
| **Total per PA** | **~60 min** | **~1 min** | **~59 min** |

For a pharmacy processing 20 PAs per day, that's **~20 hours of staff time saved daily**.
