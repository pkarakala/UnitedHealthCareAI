# Developer Handoff Guide

This document is for anyone picking up this project. It covers everything you need to get the backend running, understand the codebase, and continue development.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Prerequisites](#prerequisites)
3. [Option A: Supabase Setup (Recommended for Quick Start)](#option-a-supabase-setup)
4. [Option B: Local Docker Setup](#option-b-local-docker-setup)
5. [Anthropic API Setup](#anthropic-api-setup)
6. [Running the Backend](#running-the-backend)
7. [Database Migrations](#database-migrations)
8. [Testing the System](#testing-the-system)
9. [Codebase Map](#codebase-map)
10. [How the AI Agents Work](#how-the-ai-agents-work)
11. [Key Decisions Already Made](#key-decisions-already-made)
12. [What's Left To Do](#whats-left-to-do)
13. [Troubleshooting](#troubleshooting)

---

## Project Overview

This is an AI-powered Prior Authorization platform for pharmacies. It uses 16 specialized AI agents (powered by Anthropic's Claude) to automate the PA workflow end-to-end.

**Frontend:** https://usahealthcare.ai (existing — this backend serves as the API)
**Backend API:** FastAPI (Python 3.12) at `localhost:8000`
**Database:** PostgreSQL (via Supabase or local Docker)
**AI:** Anthropic Claude API
**Task Queue:** Celery + Redis (for scheduled background jobs)

---

## Prerequisites

Install these on your machine:

| Tool | Install | Verify |
|------|---------|--------|
| Python 3.12+ | `brew install python@3.12` | `python3 --version` |
| Docker Desktop | https://docker.com/products/docker-desktop | `docker --version` |
| Git | `brew install git` | `git --version` |
| Make | Pre-installed on Mac | `make --version` |
| curl | Pre-installed on Mac | `curl --version` |

Optional but helpful:
- **pgAdmin** or **TablePlus** for viewing the database
- **Postman** or **HTTPie** for testing API endpoints
- A code editor (VS Code recommended)

---

## Option A: Supabase Setup (Recommended for Quick Start)

Supabase gives you a hosted PostgreSQL database with a nice UI — no Docker needed for the DB layer.

### Step 1: Create a Supabase Account

1. Go to https://supabase.com
2. Click "Start your project" → Sign up with GitHub
3. Create a new organization (free tier is fine)

### Step 2: Create a New Project

1. Click "New Project"
2. Fill in:
   - **Name:** `prior-auth-platform`
   - **Database Password:** Generate a strong password and **save it somewhere safe**
   - **Region:** Choose closest to you (e.g., `us-east-1`)
3. Click "Create new project"
4. Wait ~2 minutes for it to provision

### Step 3: Enable pgvector Extension

We use pgvector for AI embeddings (RAG). Enable it in Supabase:

1. In your Supabase dashboard, go to **Database** → **Extensions**
2. Search for `vector`
3. Click **Enable** on the `vector` extension

Alternatively, run this SQL in the **SQL Editor**:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### Step 4: Get Your Connection String

1. Go to **Settings** → **Database**
2. Find the **Connection string** section
3. Select **URI** format
4. Copy the connection string — it looks like:
   ```
   postgresql://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres
   ```

5. For our async driver, modify it to use `asyncpg`:
   ```
   postgresql+asyncpg://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres
   ```

### Step 5: Configure the .env File

```bash
cd ~/Desktop/project
cp .env.example .env
```

Edit `.env`:
```env
# Database (Supabase)
DATABASE_URL=postgresql+asyncpg://postgres.[your-ref]:[your-password]@aws-0-us-east-1.pooler.supabase.com:6543/postgres

# Redis (still need local Redis for Celery)
REDIS_URL=redis://localhost:6379/0

# Anthropic (see next section)
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx

# Security
SECRET_KEY=generate-a-random-string-here
ENCRYPTION_KEY=generate-a-32-char-string-here

# CORS
CORS_ORIGINS=http://localhost:3000,https://usahealthcare.ai
```

To generate random keys:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Step 6: Start Redis Locally

You still need Redis for the task queue:
```bash
docker run -d --name redis -p 6379:6379 redis:7-alpine
```

Or install Redis directly:
```bash
brew install redis
brew services start redis
```

### Step 7: Supabase Notes

- **Free tier limits:** 500MB database, 2GB bandwidth/month — more than enough for development
- **Connection pooling:** Use port `6543` (pooler) not `5432` (direct) for better performance
- **Dashboard:** You can view/edit data directly at https://supabase.com/dashboard
- **SQL Editor:** Run queries directly in the Supabase dashboard
- **Backups:** Automatic daily backups on paid plans

---

## Option B: Local Docker Setup

If you want everything running locally in Docker:

```bash
cd ~/Desktop/project

# Copy env file
cp .env.example .env
# Edit .env with your Anthropic key (see next section)

# Start everything (PostgreSQL, Redis, API, Celery)
make up

# This starts:
# - PostgreSQL (port 5432)
# - Redis (port 6379)
# - FastAPI (port 8000)
# - Celery Worker
# - Celery Beat
# - pgAdmin (port 5050)
```

The default `.env` doesn't need DATABASE_URL changes for Docker — the `docker-compose.yml` sets it automatically.

---

## Anthropic API Setup

You need an Anthropic API key for the AI agents to work.

### Step 1: Create an Anthropic Account

1. Go to https://console.anthropic.com
2. Sign up or log in
3. Go to **API Keys** (in the left sidebar)
4. Click **Create Key**
5. Name it: `prior-auth-platform-dev`
6. Copy the key (starts with `sk-ant-api03-...`)

### Step 2: Add to .env

```env
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
```

### Step 3: Billing

- New accounts get $5 in free credits
- After that, you'll need to add a payment method
- Cost estimate: ~$0.01-0.05 per PA workflow (depends on complexity)
- Claude Sonnet 4 pricing: $3/1M input tokens, $15/1M output tokens

### Step 4: Rate Limits

Default rate limits for new accounts:
- 50 requests/minute
- 40,000 tokens/minute

For development, this is more than enough. For production, request a limit increase.

---

## Running the Backend

### With Docker (Option B):

```bash
cd ~/Desktop/project

# Start all services
make up

# Run migrations
make migrate

# Seed sample data
make seed

# Verify it works
make health
```

### Without Docker (Option A - Supabase):

```bash
cd ~/Desktop/project/backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Make sure .env is configured (see above)

# Run migrations
alembic upgrade head

# Seed sample data
python scripts/seed.py

# Start the API
uvicorn app.main:app --reload --port 8000

# In a new terminal (activate venv first):
source venv/bin/activate
celery -A app.celery_app worker --loglevel=info

# In another terminal (for scheduled tasks):
source venv/bin/activate
celery -A app.celery_app beat --loglevel=info
```

### Verify It's Running

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Should return:
# {"status":"healthy","version":"1.0.0","timestamp":"...","database":"connected","redis":"connected"}

# Open Swagger docs in browser:
open http://localhost:8000/docs
```

---

## Database Migrations

### First Time Setup

If you're starting fresh with a new database:

```bash
# Generate the initial migration (creates all tables)
cd backend
alembic revision --autogenerate -m "initial schema"

# Apply it
alembic upgrade head
```

### After Changing Models

When you modify any file in `app/models/`:

```bash
# Generate a new migration
alembic revision --autogenerate -m "describe what changed"

# Review the generated file in alembic/versions/
# Then apply:
alembic upgrade head
```

### Rollback

```bash
# Go back one migration
alembic downgrade -1

# Go back to specific revision
alembic downgrade <revision_id>
```

---

## Testing the System

### Run the Test Suite

```bash
cd backend
pip install aiosqlite  # needed for test SQLite DB
pytest tests/ -v
```

### Test a Full PA Workflow

```bash
# 1. Create a patient
curl -X POST http://localhost:8000/api/v1/patients \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "John",
    "last_name": "Doe",
    "date_of_birth": "1970-05-15",
    "phone": "5551234567",
    "member_id": "MBR12345"
  }'
# Note the patient ID from the response

# 2. Intake a prescription (this triggers the full workflow)
curl -X POST http://localhost:8000/api/v1/prescriptions/intake \
  -F "patient_id=<patient-id-from-step-1>" \
  -F "prescriber_npi=1234567890" \
  -F "drug_name=Ozempic" \
  -F "strength=1mg/dose" \
  -F "quantity=4" \
  -F "days_supply=28" \
  -F "prescriber_name=Dr. Smith" \
  -F "prescriber_fax=5555551234"

# 3. Check the PA status
curl http://localhost:8000/api/v1/prior-auths

# 4. View the execution timeline
curl http://localhost:8000/api/v1/prior-auths/<pa-id>/timeline

# 5. Manually advance the workflow
curl -X POST "http://localhost:8000/api/v1/prior-auths/<pa-id>/advance?condition=approved"

# 6. Check analytics
curl http://localhost:8000/api/v1/analytics/dashboard
```

---

## Codebase Map

```
project/
├── .env.example              ← Copy to .env, add your keys
├── docker-compose.yml        ← Docker orchestration (all services)
├── Makefile                  ← Dev commands (make up, make test, etc.)
├── README.md                 ← Project overview
│
├── docs/                     ← Human-readable documentation
│   ├── ARCHITECTURE.md       ← System design diagrams
│   ├── API_REFERENCE.md      ← Every API endpoint with examples
│   ├── AGENTS_GUIDE.md       ← How each AI agent works
│   ├── SETUP.md              ← Setup instructions
│   ├── WORKFLOW.md           ← PA workflow explained (non-technical)
│   ├── HIPAA_COMPLIANCE.md   ← Security/compliance notes
│   └── HANDOFF.md            ← THIS FILE
│
├── backend/
│   ├── Dockerfile            ← Container build
│   ├── requirements.txt      ← Python dependencies
│   ├── alembic.ini           ← Migration config
│   ├── alembic/              ← Database migrations
│   │   ├── env.py
│   │   └── versions/         ← Migration files go here
│   │
│   ├── scripts/
│   │   └── seed.py           ← Creates sample data
│   │
│   ├── tests/                ← Test suite
│   │   ├── conftest.py       ← Test fixtures
│   │   ├── test_api/         ← API endpoint tests
│   │   ├── test_agents/      ← Agent logic tests
│   │   └── test_services/    ← Service layer tests
│   │
│   └── app/                  ← Main application
│       ├── main.py           ← FastAPI app entry point
│       ├── config.py         ← Settings (reads from .env)
│       ├── database.py       ← DB connection setup
│       ├── celery_app.py     ← Background task config
│       ├── security.py       ← JWT auth, password hashing
│       │
│       ├── agents/           ← THE CORE: 16 AI agents
│       │   ├── base.py       ← BaseAgent class (all inherit from this)
│       │   ├── orchestrator.py ← State machine (routes work between agents)
│       │   ├── prescription_intake.py    ← Agent 1
│       │   ├── pa_detection.py           ← Agent 2
│       │   ├── insurance_verification.py ← Agent 3
│       │   ├── clinical_requirement.py   ← Agent 4
│       │   ├── patient_record.py         ← Agent 5
│       │   ├── doctor_communication.py   ← Agent 6
│       │   ├── followup.py              ← Agent 7
│       │   ├── pa_form_filling.py       ← Agent 8
│       │   ├── clinical_writing.py      ← Agent 9
│       │   ├── submission.py            ← Agent 10
│       │   ├── status_monitoring.py     ← Agent 11
│       │   ├── approval.py             ← Agent 12
│       │   ├── denial_analysis.py      ← Agent 13
│       │   ├── appeal.py              ← Agent 14
│       │   ├── patient_communication.py ← Agent 15
│       │   └── revenue_analytics.py    ← Agent 16
│       │
│       ├── api/v1/           ← REST API routes
│       │   ├── health.py
│       │   ├── prescriptions.py
│       │   ├── prior_auths.py   ← Main PA endpoints
│       │   ├── patients.py
│       │   ├── insurance.py
│       │   ├── communications.py
│       │   ├── appeals.py
│       │   ├── analytics.py
│       │   ├── documents.py
│       │   ├── webhooks.py
│       │   └── agents.py
│       │
│       ├── models/           ← Database tables (SQLAlchemy)
│       │   ├── base.py       ← Shared audit fields
│       │   ├── patient.py
│       │   ├── prescription.py
│       │   ├── prior_auth.py  ← Central entity
│       │   ├── insurance.py
│       │   ├── clinical_document.py
│       │   ├── communication.py
│       │   ├── appeal.py
│       │   ├── audit_log.py
│       │   └── agent_execution.py
│       │
│       ├── schemas/          ← Request/Response shapes (Pydantic)
│       ├── services/         ← Business logic
│       ├── tasks/            ← Celery background tasks
│       └── utils/            ← Shared utilities
│           ├── constants.py  ← Enums (PAStatus, AgentType, etc.)
│           ├── encryption.py ← PHI encryption (AES-256)
│           ├── validators.py ← NPI, NDC, ICD-10 validation
│           └── logging.py    ← Structured JSON logging
│
└── frontend/                 ← Placeholder (frontend is at usahealthcare.ai)
```

---

## How the AI Agents Work

Read `docs/AGENTS_GUIDE.md` for the full breakdown, but here's the quick version:

1. Every agent inherits from `BaseAgent` (in `agents/base.py`)
2. The `Orchestrator` (in `agents/orchestrator.py`) is a state machine that routes work
3. When a prescription comes in, the orchestrator runs agents in sequence
4. Each agent calls Claude with a specialized system prompt
5. Claude returns structured JSON which the agent processes
6. Results are stored in the database and the orchestrator advances to the next step

**To modify an agent's behavior:** Edit its `get_system_prompt()` method or `execute()` logic.

**To change the workflow order:** Edit `WORKFLOW_TRANSITIONS` in `orchestrator.py`.

---

## Key Decisions Already Made

| Decision | Choice | Why |
|----------|--------|-----|
| AI Provider | Anthropic Claude | User preference; strong at structured output |
| Model | Claude Sonnet 4 | Best balance of speed/cost/capability |
| Framework | FastAPI | Async-native, auto-generates OpenAPI docs |
| Database | PostgreSQL + pgvector | Mature, pgvector for RAG embeddings |
| ORM | SQLAlchemy (async) | Industry standard, migration support |
| Task Queue | Celery + Redis | Reliable scheduled tasks |
| Auth | JWT tokens | Stateless, works with frontend |
| PHI Encryption | AES-256 (Fernet) | HIPAA requirement |

---

## What's Left To Do

### High Priority (Core Functionality)
- [ ] Generate the initial Alembic migration and test it
- [ ] Connect to real Anthropic API and test each agent end-to-end
- [ ] Add `aiosqlite` to requirements.txt for test database
- [ ] Wire up the frontend (usahealthcare.ai) to call this API
- [ ] Add API key authentication to protect endpoints

### Medium Priority (Production Readiness)
- [ ] Integrate with real pharmacy systems (Rx30, PioneerRx, etc.)
- [ ] Integrate with CoverMyMeds API for actual PA submissions
- [ ] Add Twilio for SMS notifications
- [ ] Add SendGrid/SES for email notifications
- [ ] Add fax API integration (RingCentral or SRFax)
- [ ] Set up Langfuse for LLM observability
- [ ] Add rate limiting middleware

### Lower Priority (Enhancements)
- [ ] RAG pipeline: embed formulary PDFs into pgvector
- [ ] Predictive model: estimate PA approval probability before submission
- [ ] Formulary alternative suggestions
- [ ] Prescriber response time predictions
- [ ] Multi-tenant support (multiple pharmacies)

---

## Troubleshooting

### "Module not found" errors
```bash
# Make sure you're in the virtual env
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Database connection refused
```bash
# If using Docker:
docker compose ps  # check if db is running
docker compose logs db  # check for errors

# If using Supabase:
# - Check your connection string in .env
# - Make sure you're using port 6543 (pooler) not 5432
# - Check if your IP is allowlisted in Supabase dashboard
```

### Alembic "Target database is not up to date"
```bash
# Check current revision
alembic current

# If empty/behind, run:
alembic upgrade head
```

### Claude API errors
```bash
# Check your API key
echo $ANTHROPIC_API_KEY

# Test it directly:
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "content-type: application/json" \
  -H "anthropic-version: 2023-06-01" \
  -d '{"model":"claude-sonnet-4-20250514","max_tokens":100,"messages":[{"role":"user","content":"Hello"}]}'
```

### Redis connection errors
```bash
# Check if Redis is running
redis-cli ping
# Should return: PONG

# If not running:
docker run -d --name redis -p 6379:6379 redis:7-alpine
# Or: brew services start redis
```

### CORS errors from frontend
- Check `CORS_ORIGINS` in `.env` includes the frontend URL
- Make sure there's no trailing slash
- Example: `CORS_ORIGINS=http://localhost:3000,https://usahealthcare.ai`

---

## Contacts / Resources

- **Frontend:** https://usahealthcare.ai
- **API Docs:** http://localhost:8000/docs (when running)
- **Supabase Dashboard:** https://supabase.com/dashboard
- **Anthropic Console:** https://console.anthropic.com
- **Claude API Docs:** https://docs.anthropic.com/en/docs
- **FastAPI Docs:** https://fastapi.tiangolo.com
- **SQLAlchemy Docs:** https://docs.sqlalchemy.org
