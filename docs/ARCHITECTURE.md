# Architecture

## System Overview

The Prior Authorization AI Platform is a multi-agent orchestration system that automates pharmacy PA workflows. It consists of a FastAPI backend, 16 specialized AI agents coordinated by a state machine orchestrator, PostgreSQL for persistence, Redis for caching/queuing, and Celery for scheduled background tasks.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Frontend Layer                                 │
│  usahealthcare.ai (React/Next.js)  ←──── REST API ────→  Swagger UI │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        API Gateway (FastAPI)                          │
│  • CORS middleware                                                    │
│  • JWT/API Key authentication                                         │
│  • Rate limiting                                                      │
│  • Request validation (Pydantic)                                      │
│  • Audit logging                                                      │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                ┌───────────────┼───────────────┐
                ▼               ▼               ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│   API Routes     │ │   Orchestrator   │ │  Celery Workers  │
│  (REST CRUD)     │ │  (State Machine) │ │  (Background)    │
│                  │ │                  │ │                  │
│ • Prescriptions  │ │ • Workflow graph │ │ • Follow-ups     │
│ • Prior Auths    │ │ • Transitions    │ │ • Monitoring     │
│ • Patients       │ │ • Agent routing  │ │ • Notifications  │
│ • Analytics      │ │ • Auto-advance   │ │ • Analytics      │
│ • Webhooks       │ │ • Error recovery │ │                  │
└──────────────────┘ └────────┬─────────┘ └──────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        Agent Layer (16 Agents)                        │
│                                                                       │
│  ┌─────────────┐ ┌──────────────┐ ┌────────────────┐ ┌──────────┐  │
│  │  Intake     │ │  PA Detect   │ │  Insurance     │ │ Clinical │  │
│  │  Agent      │ │  Agent       │ │  Verify Agent  │ │ Req Agent│  │
│  └─────────────┘ └──────────────┘ └────────────────┘ └──────────┘  │
│  ┌─────────────┐ ┌──────────────┐ ┌────────────────┐ ┌──────────┐  │
│  │  Patient    │ │  Doctor      │ │  Follow-up     │ │ Form     │  │
│  │  Record     │ │  Comm Agent  │ │  Agent         │ │ Fill     │  │
│  └─────────────┘ └──────────────┘ └────────────────┘ └──────────┘  │
│  ┌─────────────┐ ┌──────────────┐ ┌────────────────┐ ┌──────────┐  │
│  │  Clinical   │ │  Submission  │ │  Status Mon    │ │ Approval │  │
│  │  Writing    │ │  Agent       │ │  Agent         │ │ Agent    │  │
│  └─────────────┘ └──────────────┘ └────────────────┘ └──────────┘  │
│  ┌─────────────┐ ┌──────────────┐ ┌────────────────┐ ┌──────────┐  │
│  │  Denial     │ │  Appeal      │ │  Patient       │ │ Revenue  │  │
│  │  Analysis   │ │  Agent       │ │  Comm Agent    │ │ Analytics│  │
│  └─────────────┘ └──────────────┘ └────────────────┘ └──────────┘  │
│                                                                       │
│  All agents inherit from BaseAgent:                                   │
│  • execute() — agent-specific logic                                   │
│  • get_system_prompt() — Claude instructions                          │
│  • run() — lifecycle: logging, timing, error handling                 │
│  • call_claude() — standardized API calls                            │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        Data Layer                                     │
│                                                                       │
│  ┌─────────────────────────────────────┐  ┌──────────────────────┐  │
│  │  PostgreSQL 16 + pgvector           │  │  Redis 7             │  │
│  │                                     │  │                      │  │
│  │  Tables:                            │  │  • Celery broker     │  │
│  │  • patients                         │  │  • Result backend    │  │
│  │  • prescriptions                    │  │  • Session cache     │  │
│  │  • prior_auths (central entity)     │  │  • Rate limiting     │  │
│  │  • insurances                       │  │                      │  │
│  │  • clinical_documents               │  └──────────────────────┘  │
│  │  • communications                   │                             │
│  │  • appeals                          │  ┌──────────────────────┐  │
│  │  • audit_logs                       │  │  Langfuse            │  │
│  │  • agent_executions                 │  │  (LLM Observability) │  │
│  │                                     │  │                      │  │
│  │  pgvector: formulary embeddings     │  │  • Trace every call  │  │
│  │  for RAG similarity search          │  │  • Token usage       │  │
│  └─────────────────────────────────────┘  │  • Cost tracking     │  │
│                                            └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

## Data Flow: Complete PA Lifecycle

```
Prescription Arrives (electronic, fax, scan)
        │
        ▼
[1] Prescription Intake Agent
    • OCR/Vision extracts drug, qty, prescriber
    • Stores in prescriptions table
    • Creates PriorAuth record (status: INTAKE)
        │
        ▼
[2] PA Detection Agent
    • Checks formulary status, reject codes
    • If PA not needed → status: NO_PA_REQUIRED → done
    • If PA needed → status: PA_DETECTION → continue
        │
        ▼
[3] Insurance Verification Agent
    • Verifies BIN/PCN/Member ID
    • Checks coverage, step therapy, qty limits
    • status: INSURANCE_VERIFICATION
        │
        ▼
[4] Clinical Requirement Agent
    • Identifies payer-specific requirements
    • Lists missing documentation
    • status: CLINICAL_REVIEW
        │
        ├── docs_complete ──────────────────────────┐
        ▼                                           │
[5] Patient Record Retrieval Agent                  │
    • Gathers med history, labs, ICD-10             │
    • status: AWAITING_RECORDS                      │
        │                                           │
        ▼                                           │
[6] Doctor Communication Agent                      │
    • Generates fax/email/portal outreach           │
    • Requests missing documentation                │
    • status: DOCTOR_OUTREACH                       │
        │                                           │
        ▼                                           │
[7] Follow-up Agent (runs on schedule)              │
    • Day 1: Reminder                               │
    • Day 2: Phone call                             │
    • Day 4: Multi-channel                          │
    • Day 6: Escalate                               │
    • status: FOLLOWUP_PENDING                      │
        │                                           │
        ├── docs received ──────────────────────────┤
        ▼                                           ▼
[8] PA Form Filling Agent ◀─────────────────────────┘
    • Maps data to PA form fields
    • Determines submission platform
    • status: FORM_FILLING
        │
        ▼
[9] Clinical Writing Agent
    • Generates medical necessity letter
    • Compiles clinical summary
    • status: CLINICAL_WRITING
        │
        ▼
[10] Submission Agent
     • Submits via ePA/CoverMyMeds/fax/portal
     • Logs confirmation number
     • status: SUBMITTED → PENDING_REVIEW
        │
        ▼
[11] Status Monitoring Agent (runs every 2 hours)
     • Checks portal/API for decision
     • status: PENDING_REVIEW (loops until decision)
        │
        ├── APPROVED ──────────────────┐
        │                              ▼
        │                   [12] Approval Agent
        │                       • Updates pharmacy system
        │                       • Reverses/rebills claim
        │                       • Notifies technician
        │                              │
        ├── DENIED ────────────────────┤
        │                              │
        ▼                              │
[13] Denial Analysis Agent             │
     • Identifies root cause           │
     • Determines if appealable        │
        │                              │
        ├── appealable                 │
        ▼                              │
[14] Appeal Agent                      │
     • Drafts appeal letter            │
     • Cites clinical guidelines       │
     • Resubmits via [10]             │
        │                              │
        └──────────────────────────────┤
                                       ▼
[15] Patient Communication Agent
     • SMS: "Your Rx was approved"
     • Email: Detailed status update
     • status: COMPLETED
        │
        ▼
[16] Revenue Analytics Agent (background)
     • Computes approval rates, revenue, turnaround
     • Powers the pharmacy dashboard
```

## Key Design Decisions

### 1. State Machine Orchestration
The `Orchestrator` class manages workflow state via a transition map. Each state has defined transitions with conditions. This allows:
- Deterministic, auditable workflow progression
- Easy addition of new states/agents
- Idempotent re-execution (safe to retry)
- Human-in-the-loop at any point

### 2. Agent Architecture (BaseAgent Pattern)
Every agent inherits from `BaseAgent` which provides:
- **Lifecycle management**: DB logging, timing, error handling
- **Standardized Claude calls**: `call_claude_text()`, `call_claude_json()`
- **Execution recording**: Every agent run is logged with inputs, outputs, tokens, duration
- **Context passing**: `AgentContext` carries IDs needed to load relevant data

### 3. Async-First Design
All database operations and API calls use async/await via:
- `asyncpg` for PostgreSQL
- `httpx` for HTTP
- `anthropic.AsyncAnthropic` for Claude
This allows handling many concurrent PA workflows efficiently.

### 4. Celery for Scheduled Work
Background tasks that run on a schedule:
- **Status monitoring**: Every 2 hours, check pending PAs
- **Follow-ups**: Every hour, process escalation timelines
- **Analytics**: Nightly metric computation
- **Notifications**: Async delivery of SMS/email/fax

### 5. HIPAA-Conscious Architecture
- Field-level encryption for PHI (AES-256)
- Immutable audit log for all data access
- JWT auth with role-based access control
- Minimum-necessary data exposure per agent

## Entity Relationship Diagram

```
┌──────────────┐     ┌───────────────────┐     ┌──────────────┐
│   Patient    │────▶│   Prescription    │────▶│  Prior Auth  │
│              │     │                   │     │  (central)   │
│ • name       │     │ • drug_name       │     │              │
│ • DOB        │     │ • prescriber      │     │ • status     │
│ • member_id  │     │ • quantity        │     │ • decision   │
│ • insurance  │     │ • directions      │     │ • pa_number  │
└──────┬───────┘     └───────────────────┘     └──────┬───────┘
       │                                              │
       │         ┌────────────────────────────────────┤
       │         │              │              │      │
       │         ▼              ▼              ▼      ▼
       │  ┌────────────┐┌────────────┐┌──────────┐┌─────────────────┐
       │  │  Clinical  ││Communication││  Appeal  ││Agent Execution  │
       │  │  Document  ││            ││          ││                 │
       │  │            ││ • channel  ││ • letter ││ • agent_name    │
       │  │ • type     ││ • body     ││ • status ││ • tokens        │
       │  │ • content  ││ • status   ││ • refs   ││ • duration      │
       │  └────────────┘└────────────┘└──────────┘└─────────────────┘
       │
       ▼
┌──────────────┐
│  Insurance   │
│              │
│ • plan_name  │
│ • BIN/PCN    │
│ • formulary  │
│ • PA rules   │
└──────────────┘
```

## Service Boundaries

| Service | Responsibility | Port |
|---------|---------------|------|
| API (FastAPI) | HTTP routes, request handling | 8000 |
| Celery Worker | Background task execution | — |
| Celery Beat | Task scheduling | — |
| PostgreSQL | Primary data store | 5432 |
| Redis | Message broker + cache | 6379 |
| pgAdmin | Database management UI | 5050 |
| Langfuse | LLM observability | 3001 |

## Scaling Considerations

For production deployment:
1. **Horizontal API scaling**: Multiple API pods behind a load balancer
2. **Worker scaling**: Multiple Celery workers with separate queues per priority
3. **Database**: Read replicas for analytics queries
4. **Redis**: Redis Cluster for high availability
5. **AI calls**: Rate limiting and retry with exponential backoff
6. **Kubernetes**: Deploy via Helm charts on EKS
