import uuid
from datetime import date

import pytest
from httpx import AsyncClient

from app.models.patient import Patient
from app.models.prescription import Prescription
from app.models.prior_auth import PriorAuth


@pytest.mark.asyncio
async def test_list_prior_auths_empty(client: AsyncClient):
    response = await client.get("/api/v1/prior-auths")
    assert response.status_code == 200
    assert response.json() == []


async def _seed_pa(db_session) -> str:
    patient = Patient(
        id=str(uuid.uuid4()), first_name="P", last_name="Q",
        date_of_birth=date(1990, 1, 1),
    )
    rx = Prescription(
        id=str(uuid.uuid4()), patient_id=patient.id,
        prescriber_npi="1234567890", drug_name="Ozempic",
    )
    pa = PriorAuth(
        id=str(uuid.uuid4()), patient_id=patient.id, prescription_id=rx.id,
        status="pending_review",
    )
    db_session.add_all([patient, rx, pa])
    await db_session.commit()
    return pa.id


@pytest.mark.asyncio
async def test_update_allows_human_editable_fields(client: AsyncClient, db_session):
    pa_id = await _seed_pa(db_session)
    resp = await client.put(f"/api/v1/prior-auths/{pa_id}", json={
        "notes": "call pharmacy back",
        "priority": 2,
        "assigned_to": "tech-1",
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["notes"] == "call pharmacy back"
    assert body["priority"] == 2


@pytest.mark.asyncio
async def test_update_rejects_status_bypass(client: AsyncClient, db_session):
    pa_id = await _seed_pa(db_session)
    # Attempting to flip status/decision via PUT must be refused (422), not
    # silently applied — that would bypass the workflow state machine.
    resp = await client.put(f"/api/v1/prior-auths/{pa_id}", json={
        "status": "approved",
        "decision": "approved",
    })
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_get_prior_auth_not_found(client: AsyncClient):
    response = await client.get("/api/v1/prior-auths/nonexistent")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_cancel_prior_auth_not_found(client: AsyncClient):
    response = await client.post("/api/v1/prior-auths/nonexistent/cancel")
    assert response.status_code == 404
