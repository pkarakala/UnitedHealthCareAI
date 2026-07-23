import uuid
from datetime import date
from unittest.mock import patch

import pytest
from httpx import AsyncClient

from app.config import settings
from app.models.patient import Patient


async def _make_patient(db_session) -> str:
    patient = Patient(
        id=str(uuid.uuid4()),
        first_name="Flow",
        last_name="Test",
        date_of_birth=date(1990, 1, 1),
    )
    db_session.add(patient)
    await db_session.commit()
    return patient.id


@pytest.mark.asyncio
async def test_intake_dispatches_to_celery_when_async_enabled(client: AsyncClient, db_session):
    patient_id = await _make_patient(db_session)

    with patch.object(settings, "async_workflow", True), \
         patch("app.tasks.workflow_tasks.run_pa_workflow.delay") as mock_delay:
        resp = await client.post("/api/v1/prescriptions/intake", data={
            "patient_id": patient_id,
            "prescriber_npi": "1234567890",
            "drug_name": "Ozempic",
        })

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "workflow_queued"
    # The multi-agent workflow was handed to Celery, not run inline.
    mock_delay.assert_called_once_with(body["prior_auth_id"])


@pytest.mark.asyncio
async def test_intake_runs_inline_when_async_disabled(client: AsyncClient, db_session, mock_anthropic):
    patient_id = await _make_patient(db_session)

    with patch.object(settings, "async_workflow", False):
        resp = await client.post("/api/v1/prescriptions/intake", data={
            "patient_id": patient_id,
            "prescriber_npi": "1234567890",
            "drug_name": "Ozempic",
        })

    assert resp.status_code == 200
    assert resp.json()["status"] == "workflow_started"
