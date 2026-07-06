import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_patient(client: AsyncClient):
    response = await client.post("/api/v1/patients", json={
        "first_name": "Test",
        "last_name": "Patient",
        "date_of_birth": "1990-01-15",
        "phone": "5551234567",
        "email": "test@example.com",
        "member_id": "MBR999",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["first_name"] == "Test"
    assert data["last_name"] == "Patient"
    assert "id" in data


@pytest.mark.asyncio
async def test_list_patients(client: AsyncClient):
    # Create a patient first
    await client.post("/api/v1/patients", json={
        "first_name": "List",
        "last_name": "Test",
        "date_of_birth": "1985-06-20",
    })

    response = await client.get("/api/v1/patients")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_get_patient_not_found(client: AsyncClient):
    response = await client.get("/api/v1/patients/nonexistent-id")
    assert response.status_code == 404
