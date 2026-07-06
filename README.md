# Prior Authorization AI Platform

An AI-powered orchestration platform that automates the entire pharmacy prior authorization workflow — from prescription intake through submission, monitoring, appeals, patient communication, and revenue analytics.

## What This Does

Prior authorization is a manual, time-consuming process that costs pharmacies hours of staff time per PA. This platform uses 16 specialized AI agents (powered by Claude) to automate the workflow end-to-end:

1. **Intake** — Reads prescriptions via OCR/Vision
2. **Detection** — Determines if PA is required
3. **Insurance Verification** — Checks eligibility and coverage
4. **Clinical Requirements** — Identifies what documentation is needed
5. **Patient Records** — Retrieves clinical data
6. **Doctor Communication** — Generates outreach to prescribers
7. **Follow-up** — Manages escalation timelines
8. **Form Filling** — Completes PA forms automatically
9. **Clinical Writing** — Generates medical necessity letters
10. **Submission** — Submits via ePA/CoverMyMeds/fax
11. **Status Monitoring** — Polls for decisions
12. **Approval Processing** — Handles approved PAs
13. **Denial Analysis** — Identifies why PAs were denied
14. **Appeal** — Drafts appeal letters with clinical evidence
15. **Patient Communication** — Sends SMS/email/phone notifications
16. **Revenue Analytics** — Tracks metrics and ROI

## Quick Start

```bash
# 1. Clone and configure
cp .env.example .env
# Edit .env with your Anthropic API key

# 2. Start everything
make up

# 3. Run database migrations
make migrate

# 4. Seed sample data
make seed

# 5. Verify it's running
make health
```

The API will be available at `http://localhost:8000`.
API docs (Swagger): `http://localhost:8000/docs`

## Architecture

```
usahealthcare.ai (Frontend)
        │
   [REST API - Port 8000]
        │
┌───────────────┐
│  FastAPI GW   │
└───────┬───────┘
        │
┌───────┴───────┐     ┌────────────┐
│  Orchestrator │────▶│  Celery    │
│  (State Mach) │     │  Workers   │
└───────┬───────┘     └────────────┘
        │
┌───────┴───────┐
│  16 AI Agents │  (Claude API)
└───────┬───────┘
        │
┌───────┴───────┐     ┌───────────┐
│  PostgreSQL   │     │   Redis   │
│  + pgvector   │     │           │
└───────────────┘     └───────────┘
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| API | Python 3.12, FastAPI, Pydantic v2 |
| AI | Anthropic Claude (via SDK) |
| Database | PostgreSQL 16 + pgvector |
| Cache/Queue | Redis 7 |
| Task Queue | Celery |
| ORM | SQLAlchemy (async) |
| Migrations | Alembic |
| Containers | Docker Compose |
| Observability | Langfuse, structlog |

## Documentation

| Document | Description |
|----------|------------|
| **[Handoff Guide](docs/HANDOFF.md)** | **START HERE — Complete onboarding for new developers** |
| [Architecture](docs/ARCHITECTURE.md) | System design, data flow, component details |
| [API Reference](docs/API_REFERENCE.md) | All endpoints with examples |
| [Agents Guide](docs/AGENTS_GUIDE.md) | How each of the 16 agents works |
| [Setup Guide](docs/SETUP.md) | Detailed local development setup |
| [Workflow](docs/WORKFLOW.md) | PA workflow state machine explained (non-technical) |
| [HIPAA Compliance](docs/HIPAA_COMPLIANCE.md) | Security and compliance notes |

## Project Structure

```
project/
├── docker-compose.yml          # Full stack orchestration
├── Makefile                    # Developer commands
├── .env.example                # Environment template
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic/               # Database migrations
│   ├── app/
│   │   ├── main.py            # FastAPI application
│   │   ├── config.py          # Settings
│   │   ├── database.py        # DB connection
│   │   ├── celery_app.py      # Task queue
│   │   ├── security.py        # Auth (JWT)
│   │   ├── agents/            # 16 AI agents + orchestrator
│   │   ├── api/v1/            # REST endpoints
│   │   ├── models/            # SQLAlchemy models
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── services/          # Business logic
│   │   ├── tasks/             # Celery scheduled tasks
│   │   └── utils/             # Shared utilities
│   ├── scripts/               # Seed data, utilities
│   └── tests/                 # Test suite
├── docs/                      # Human-readable documentation
└── frontend/                  # Minimal dashboard (reference)
```

## Key Commands

```bash
make up              # Start all services
make down            # Stop all services
make logs            # Follow API logs
make logs-worker     # Follow Celery worker logs
make migrate         # Run database migrations
make test            # Run test suite
make seed            # Seed sample data
make health          # Check API health
make shell           # Shell into API container
make db-shell        # PostgreSQL shell
```

## Frontend Integration

The API is designed to connect with the existing frontend at https://usahealthcare.ai.
CORS is configured to allow requests from that domain. The API follows REST conventions
with consistent response formats for easy integration.

## License

Proprietary — All rights reserved.
