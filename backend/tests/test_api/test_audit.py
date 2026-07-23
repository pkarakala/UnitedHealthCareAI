import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.models.audit_log import AuditLog


@pytest.mark.asyncio
async def test_patient_read_writes_audit_log(client: AsyncClient, db_session):
    create = await client.post("/api/v1/patients", json={
        "first_name": "Audit",
        "last_name": "Target",
        "date_of_birth": "1980-02-02",
        "phone": "5550001111",
    })
    patient_id = create.json()["id"]

    resp = await client.get(f"/api/v1/patients/{patient_id}")
    assert resp.status_code == 200

    rows = (await db_session.execute(select(AuditLog))).scalars().all()
    actions = {(r.action, r.resource_type) for r in rows}
    assert ("create", "patient") in actions
    assert ("read", "patient") in actions
    read_row = next(r for r in rows if r.action == "read" and r.resource_type == "patient")
    assert read_row.resource_id == patient_id
    assert read_row.phi_accessed is True


@pytest.mark.asyncio
async def test_patient_read_response_returns_decrypted_phi(client: AsyncClient):
    create = await client.post("/api/v1/patients", json={
        "first_name": "Cipher",
        "last_name": "Check",
        "date_of_birth": "1975-03-03",
        "phone": "5552223333",
        "email": "cipher.check@example.com",
    })
    patient_id = create.json()["id"]

    resp = await client.get(f"/api/v1/patients/{patient_id}")
    body = resp.json()
    # API sees plaintext even though the column is encrypted at rest.
    assert body["phone"] == "5552223333"
    assert body["email"] == "cipher.check@example.com"
