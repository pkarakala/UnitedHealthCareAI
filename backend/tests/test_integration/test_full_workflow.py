"""
Full end-to-end integration test for the PA workflow.
Mocks Claude API responses to test the complete orchestrator pipeline.
"""
import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.main import app
from app.database import get_db
from app.models.base import Base
from app.models.prior_auth import PriorAuth
from app.models.agent_execution import AgentExecution
from app.models.user import User
from app.security import get_current_user
from app.utils.constants import PAStatus

TEST_USER = User(
    id="itest-user-id",
    email="itest@pharmacy.test",
    hashed_password="not-a-real-hash",
    role="admin",
    is_active=True,
)

TEST_DB_URL = "sqlite+aiosqlite:///./test_integration.db"
engine = create_async_engine(TEST_DB_URL, echo=False)
TestSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


def mock_claude_response(data: dict):
    """Create a mock Anthropic API response."""
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text=json.dumps(data))]
    mock_msg.usage = MagicMock(input_tokens=150, output_tokens=80)
    return mock_msg


# Claude responses for each agent in the workflow
MOCK_RESPONSES = {
    "prescription_intake": {
        "drug_name": "Ozempic",
        "strength": "1mg/dose",
        "quantity": 4,
        "days_supply": 28,
        "directions": "Inject 1mg subcutaneously once weekly",
        "prescriber_name": "Dr. Smith",
        "prescriber_npi": "1234567890",
        "ndc": "00169416112",
        "diagnosis_codes": ["E11.65"],
        "confidence": 0.95,
        "flags": [],
    },
    "pa_detection": {
        "pa_required": True,
        "reason": "Non-preferred specialty drug requiring step therapy",
        "reject_codes": ["75"],
        "formulary_status": "non_preferred",
        "step_therapy_required": True,
        "quantity_limit_exceeded": False,
        "alternatives": ["Trulicity", "Victoza"],
        "urgency": "routine",
        "confidence": 0.92,
    },
    "insurance_verification": {
        "is_active": True,
        "plan_name": "BCBS PPO",
        "coverage_type": "commercial",
        "drug_tier": "tier3_nonpreferred",
        "copay_estimate": 150.0,
        "deductible_remaining": 500.0,
        "step_therapy_required": True,
        "step_therapy_drugs": ["metformin", "glipizide"],
        "quantity_limit_applies": False,
        "age_restriction": False,
        "diagnosis_restriction": True,
        "required_diagnosis_codes": ["E11.x"],
        "prior_auth_form": "BCBS Standard PA",
        "submission_method": "covermymeds",
        "portal_url": "https://provider.bcbs.com",
        "notes": "Active coverage verified",
    },
    "clinical_requirement": {
        "required_diagnoses": ["E11.65 - Type 2 diabetes with hyperglycemia"],
        "required_labs": ["HbA1c > 7% within last 6 months"],
        "required_prior_therapies": ["Metformin 3+ months", "One other oral agent"],
        "step_therapy_drugs": ["metformin", "glipizide", "jardiance"],
        "documentation_needed": ["Recent A1c lab", "Clinical notes", "Medication history"],
        "missing_items": ["Recent HbA1c result", "Documentation of metformin failure"],
        "complexity": "moderate",
        "estimated_approval_probability": 0.75,
    },
    "patient_record": {
        "medications_current": [{"drug": "Metformin", "dose": "1000mg BID", "start": "2023-01-15"}],
        "medications_history": [
            {"drug": "Metformin", "duration": "18 months", "status": "active"},
            {"drug": "Glipizide", "duration": "6 months", "status": "discontinued", "reason": "inadequate control"},
        ],
        "allergies": ["Sulfonamides"],
        "diagnoses": [{"code": "E11.65", "description": "Type 2 diabetes with hyperglycemia", "date": "2022-06-01"}],
        "lab_results": [{"test": "HbA1c", "value": "9.4", "unit": "%", "date": "2024-11-15", "normal_range": "4.0-5.6"}],
        "therapy_failures": [
            {"drug": "Glipizide", "duration": "6 months", "reason": "A1c remained >8%"},
        ],
        "data_gaps": [],
    },
}


@pytest.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session():
    async with TestSessionLocal() as session:
        yield session


@pytest.fixture
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: TEST_USER
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


def create_anthropic_mock():
    """Create a mock that returns different responses based on the system prompt."""
    mock_client = AsyncMock()

    call_count = {"n": 0}

    async def mock_create(**kwargs):
        call_count["n"] += 1
        # Determine which agent is calling based on system prompt or messages
        system = kwargs.get("system", "")
        messages = kwargs.get("messages", [])
        user_content = messages[0]["content"] if messages else ""

        if "prescription intake" in system.lower():
            data = MOCK_RESPONSES["prescription_intake"]
        elif "pa detection" in system.lower() or "prior authorization detection" in system.lower():
            data = MOCK_RESPONSES["pa_detection"]
        elif "insurance verification" in system.lower():
            data = MOCK_RESPONSES["insurance_verification"]
        elif "clinical requirements" in system.lower() or "clinical requirement" in system.lower():
            data = MOCK_RESPONSES["clinical_requirement"]
        elif "patient medical records" in system.lower() or "patient record" in system.lower():
            data = MOCK_RESPONSES["patient_record"]
        else:
            data = {"success": True, "message": "Processed"}

        return mock_claude_response(data)

    mock_client.messages.create = mock_create
    return mock_client


@pytest.mark.asyncio
async def test_full_pa_workflow_intake_to_clinical_review(client: AsyncClient, db_session: AsyncSession):
    """
    Test the full workflow from prescription intake through clinical review.
    This covers agents 1-4 which run synchronously during intake.
    """
    with patch("anthropic.AsyncAnthropic") as mock_anthropic_class:
        mock_anthropic_class.return_value = create_anthropic_mock()

        # Step 1: Create a patient
        patient_response = await client.post("/api/v1/patients", json={
            "first_name": "John",
            "last_name": "Smith",
            "date_of_birth": "1965-03-15",
            "phone": "5551234567",
            "email": "john@test.com",
            "member_id": "MBR001234",
        })
        assert patient_response.status_code == 200
        patient = patient_response.json()
        patient_id = patient["id"]

        # Step 2: Intake a prescription (triggers workflow)
        intake_response = await client.post(
            "/api/v1/prescriptions/intake",
            data={
                "patient_id": patient_id,
                "prescriber_npi": "1234567890",
                "drug_name": "Ozempic",
                "strength": "1mg/dose",
                "quantity": "4",
                "days_supply": "28",
                "prescriber_name": "Dr. Smith",
                "prescriber_fax": "5555551234",
            },
        )
        assert intake_response.status_code == 200
        intake_data = intake_response.json()
        assert "prior_auth_id" in intake_data
        assert "prescription_id" in intake_data
        pa_id = intake_data["prior_auth_id"]

        # Step 3: Verify PA was created
        pa_response = await client.get(f"/api/v1/prior-auths/{pa_id}")
        assert pa_response.status_code == 200
        pa = pa_response.json()
        assert pa["patient_id"] == patient_id
        assert pa["id"] == pa_id

        # Step 4: Check the timeline has agent executions
        timeline_response = await client.get(f"/api/v1/prior-auths/{pa_id}/timeline")
        assert timeline_response.status_code == 200
        timeline = timeline_response.json()
        assert len(timeline["events"]) >= 1


@pytest.mark.asyncio
async def test_patient_crud(client: AsyncClient):
    """Test patient create, read, update, list operations."""
    # Create
    response = await client.post("/api/v1/patients", json={
        "first_name": "Test",
        "last_name": "User",
        "date_of_birth": "1990-01-01",
        "phone": "5559999999",
    })
    assert response.status_code == 200
    patient = response.json()
    assert patient["first_name"] == "Test"

    # Read
    response = await client.get(f"/api/v1/patients/{patient['id']}")
    assert response.status_code == 200
    assert response.json()["last_name"] == "User"

    # Update
    response = await client.put(f"/api/v1/patients/{patient['id']}", json={
        "phone": "5558888888",
    })
    assert response.status_code == 200
    assert response.json()["phone"] == "5558888888"

    # List
    response = await client.get("/api/v1/patients")
    assert response.status_code == 200
    assert len(response.json()) >= 1

    # Search
    response = await client.get("/api/v1/patients?search=Test")
    assert response.status_code == 200
    assert len(response.json()) >= 1


@pytest.mark.asyncio
async def test_analytics_dashboard(client: AsyncClient):
    """Test that analytics endpoints return valid data."""
    response = await client.get("/api/v1/analytics/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert "total_pas" in data
    assert "approval_rate" in data
    assert "revenue_recovered_mtd" in data


@pytest.mark.asyncio
async def test_agent_types_list(client: AsyncClient):
    """Test that all 16 agent types are listed."""
    response = await client.get("/api/v1/agents/types")
    assert response.status_code == 200
    data = response.json()
    assert len(data["agents"]) == 16


@pytest.mark.asyncio
async def test_insurance_verification(client: AsyncClient):
    """Test insurance verification endpoint."""
    response = await client.post("/api/v1/insurance/verify", json={
        "member_id": "MBR001234",
        "bin_number": "003585",
        "pcn": "MEDDADV",
        "group_number": "GRP001",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_prior_auth_cancel(client: AsyncClient, db_session: AsyncSession):
    """Test cancelling a PA."""
    # Create patient and PA
    patient_response = await client.post("/api/v1/patients", json={
        "first_name": "Cancel",
        "last_name": "Test",
        "date_of_birth": "1980-06-15",
    })
    patient_id = patient_response.json()["id"]

    # Create prescription directly
    rx_response = await client.post("/api/v1/prescriptions", json={
        "patient_id": patient_id,
        "prescriber_npi": "9876543210",
        "drug_name": "TestDrug",
    })
    rx_id = rx_response.json()["id"]

    # Create PA
    pa_response = await client.post("/api/v1/prior-auths", json={
        "patient_id": patient_id,
        "prescription_id": rx_id,
    })
    pa_id = pa_response.json()["id"]

    # Cancel it
    cancel_response = await client.post(f"/api/v1/prior-auths/{pa_id}/cancel")
    assert cancel_response.status_code == 200

    # Verify cancelled
    pa = await client.get(f"/api/v1/prior-auths/{pa_id}")
    assert pa.json()["status"] == "cancelled"


@pytest.mark.asyncio
async def test_prior_auth_escalate(client: AsyncClient):
    """Test escalating a PA to human review."""
    # Create patient + prescription + PA
    patient_response = await client.post("/api/v1/patients", json={
        "first_name": "Escalate",
        "last_name": "Test",
        "date_of_birth": "1975-11-20",
    })
    patient_id = patient_response.json()["id"]

    rx_response = await client.post("/api/v1/prescriptions", json={
        "patient_id": patient_id,
        "prescriber_npi": "1111111111",
        "drug_name": "ComplexDrug",
    })
    rx_id = rx_response.json()["id"]

    pa_response = await client.post("/api/v1/prior-auths", json={
        "patient_id": patient_id,
        "prescription_id": rx_id,
    })
    pa_id = pa_response.json()["id"]

    # Escalate
    escalate_response = await client.post(
        f"/api/v1/prior-auths/{pa_id}/escalate?assigned_to=PharmacistJane"
    )
    assert escalate_response.status_code == 200

    # Verify escalated
    pa = await client.get(f"/api/v1/prior-auths/{pa_id}")
    assert pa.json()["escalated"] is True
    assert pa.json()["assigned_to"] == "PharmacistJane"
