import hashlib
import hmac
import json
import uuid
from datetime import date

import pytest

from app.config import settings
from app.models.patient import Patient
from app.models.prescription import Prescription
from app.models.prior_auth import PriorAuth


def sign(body: bytes, secret: str) -> str:
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


@pytest.fixture
def webhook_secret(monkeypatch):
    monkeypatch.setattr(settings, "webhook_secret", "test-webhook-secret")
    return "test-webhook-secret"


@pytest.fixture
async def submitted_pa(db_session):
    patient = Patient(
        id=str(uuid.uuid4()),
        first_name="Jane",
        last_name="Doe",
        date_of_birth=date(1980, 1, 1),
    )
    rx = Prescription(
        id=str(uuid.uuid4()),
        patient_id=patient.id,
        prescriber_npi="1234567890",
        drug_name="Ozempic",
    )
    pa = PriorAuth(
        id=str(uuid.uuid4()),
        patient_id=patient.id,
        prescription_id=rx.id,
        status="pending_review",
        pa_number="PA-TEST-123",
    )
    db_session.add_all([patient, rx, pa])
    await db_session.commit()
    return pa


@pytest.mark.asyncio
async def test_webhook_rejected_without_signature(anon_client, webhook_secret):
    resp = await anon_client.post("/api/v1/webhooks/covermymeds", json={"pa_id": "x"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_webhook_rejected_with_bad_signature(anon_client, webhook_secret):
    body = json.dumps({"pa_id": "x", "status": "approved"}).encode()
    resp = await anon_client.post(
        "/api/v1/webhooks/covermymeds",
        content=body,
        headers={
            "X-Webhook-Signature": "0" * 64,
            "Content-Type": "application/json",
        },
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_webhook_rejected_when_secret_unset(anon_client, monkeypatch):
    monkeypatch.setattr(settings, "webhook_secret", "")
    resp = await anon_client.post("/api/v1/webhooks/covermymeds", json={"pa_id": "x"})
    assert resp.status_code == 503


@pytest.mark.asyncio
async def test_webhook_accepts_valid_signature(anon_client, webhook_secret, submitted_pa, mock_anthropic):
    body = json.dumps({"pa_id": "PA-TEST-123", "status": "pending"}).encode()
    resp = await anon_client.post(
        "/api/v1/webhooks/covermymeds",
        content=body,
        headers={
            "X-Webhook-Signature": sign(body, webhook_secret),
            "Content-Type": "application/json",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["received"] is True


@pytest.mark.asyncio
async def test_webhook_unknown_status_not_processed(anon_client, webhook_secret, submitted_pa):
    body = json.dumps({"pa_id": "PA-TEST-123", "status": "exploded"}).encode()
    resp = await anon_client.post(
        "/api/v1/webhooks/covermymeds",
        content=body,
        headers={
            "X-Webhook-Signature": sign(body, webhook_secret),
            "Content-Type": "application/json",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["processed"] is False
