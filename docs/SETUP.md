# Setup Guide

Step-by-step instructions to get the Prior Authorization AI Platform running locally.

## Prerequisites

- **Docker Desktop** (includes Docker Compose)
- **Python 3.12+** (for local development without Docker)
- **Anthropic API Key** (for Claude AI agent functionality)
- **Git** (for version control)

## Step 1: Clone and Configure

```bash
cd ~/Desktop/project

# Copy the environment template
cp .env.example .env
```

Edit `.env` and set your Anthropic API key:
```
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
```

All other defaults work for local development.

## Step 2: Start the Stack

```bash
# Build and start all services
make up

# Or equivalently:
docker compose up -d
```

This starts:
| Service | Port | Description |
|---------|------|-------------|
| api | 8000 | FastAPI backend |
| celery-worker | — | Background task processor |
| celery-beat | — | Task scheduler |
| db | 5432 | PostgreSQL + pgvector |
| redis | 6379 | Cache and message broker |
| pgadmin | 5050 | Database admin UI |

## Step 3: Run Database Migrations

```bash
make migrate

# Or:
docker compose exec api alembic upgrade head
```

If you haven't generated the initial migration yet:
```bash
docker compose exec api alembic revision --autogenerate -m "initial"
docker compose exec api alembic upgrade head
```

## Step 4: Seed Sample Data

```bash
make seed

# Or:
docker compose exec api python scripts/seed.py
```

This creates:
- 2 sample insurance plans (BCBS, Aetna)
- 2 sample patients
- 2 sample prescriptions (Ozempic, Dupixent)

## Step 5: Verify

```bash
# Check health
make health
# Should return: {"status": "healthy", ...}

# Or:
curl http://localhost:8000/api/v1/health
```

## Step 6: Explore the API

Open Swagger UI in your browser:
```
http://localhost:8000/docs
```

Try some requests:
```bash
# List patients
curl http://localhost:8000/api/v1/patients

# List prescriptions
curl http://localhost:8000/api/v1/prescriptions

# Check analytics dashboard
curl http://localhost:8000/api/v1/analytics/dashboard
```

## Step 7: Run a PA Workflow

```bash
# Intake a prescription (triggers the full workflow)
curl -X POST http://localhost:8000/api/v1/prescriptions/intake \
  -F "patient_id=<patient-uuid-from-seed>" \
  -F "prescriber_npi=1234567890" \
  -F "drug_name=Ozempic" \
  -F "strength=1mg/dose" \
  -F "quantity=4" \
  -F "days_supply=28"
```

This will:
1. Create a prescription record
2. Create a PA case
3. Run the Prescription Intake Agent
4. Run the PA Detection Agent
5. Continue through the workflow automatically

Check the timeline:
```bash
curl http://localhost:8000/api/v1/prior-auths/<pa-id>/timeline
```

## Development Without Docker

If you prefer running Python directly:

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql+asyncpg://pa_user:pa_pass@localhost:5432/prior_auth"
export REDIS_URL="redis://localhost:6379/0"
export ANTHROPIC_API_KEY="sk-ant-..."

# Run the API
uvicorn app.main:app --reload --port 8000

# In another terminal, run Celery worker
celery -A app.celery_app worker --loglevel=info

# In another terminal, run Celery beat
celery -A app.celery_app beat --loglevel=info
```

Note: You'll still need PostgreSQL and Redis running (via Docker or locally installed).

## Running Tests

```bash
# With Docker
make test

# Local
cd backend
pytest tests/ -v

# With coverage
pytest tests/ -v --cov=app --cov-report=html
```

## Useful Commands

```bash
make logs            # Follow API logs
make logs-worker     # Follow Celery logs
make shell           # Shell into API container
make db-shell        # PostgreSQL interactive shell
make redis-cli       # Redis CLI
make clean           # Remove all containers and volumes
```

## Troubleshooting

### "Connection refused" on port 8000
- Check if containers are running: `docker compose ps`
- Check API logs: `make logs`
- Ensure port 8000 isn't in use: `lsof -i :8000`

### Database connection errors
- Wait 10 seconds after `make up` (DB needs to initialize)
- Check DB health: `docker compose exec db pg_isready -U pa_user`

### Agent errors (Claude API)
- Verify your `ANTHROPIC_API_KEY` in `.env`
- Check API logs for specific error messages
- Agents will return `requires_human=true` on failures

### Celery tasks not running
- Check worker logs: `make logs-worker`
- Verify Redis connection: `make redis-cli` then `PING`

## pgAdmin Access

Navigate to `http://localhost:5050`
- Email: `admin@local.dev`
- Password: `admin`

Add the server:
- Host: `db`
- Port: `5432`
- Username: `pa_user`
- Password: `pa_pass`
- Database: `prior_auth`
