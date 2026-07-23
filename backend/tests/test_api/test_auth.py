import uuid

import pytest

from app.models.user import User
from app.security import hash_password


@pytest.fixture
def make_user(db_session):
    async def _make(email="staff@example.com", password="s3cret!pass", role="pharmacist"):
        user = User(
            id=str(uuid.uuid4()),
            email=email,
            hashed_password=hash_password(password),
            full_name="Test Pharmacist",
            role=role,
        )
        db_session.add(user)
        await db_session.commit()
        return user

    return _make


@pytest.mark.asyncio
async def test_protected_endpoints_require_auth(anon_client):
    for path in ["/api/v1/patients", "/api/v1/prior-auths", "/api/v1/analytics/dashboard"]:
        resp = await anon_client.get(path)
        assert resp.status_code == 401, path


@pytest.mark.asyncio
async def test_login_success_and_me(anon_client, make_user):
    await make_user()
    resp = await anon_client.post(
        "/api/v1/auth/login",
        json={"email": "staff@example.com", "password": "s3cret!pass"},
    )
    assert resp.status_code == 200
    token = resp.json()["access_token"]

    me = await anon_client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "staff@example.com"

    # Token also unlocks protected endpoints
    patients = await anon_client.get("/api/v1/patients", headers={"Authorization": f"Bearer {token}"})
    assert patients.status_code == 200


@pytest.mark.asyncio
async def test_login_wrong_password(anon_client, make_user):
    await make_user()
    resp = await anon_client.post(
        "/api/v1/auth/login",
        json={"email": "staff@example.com", "password": "wrong"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_unknown_email(anon_client):
    resp = await anon_client.post(
        "/api/v1/auth/login",
        json={"email": "ghost@example.com", "password": "whatever"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_create_user_requires_admin(anon_client, make_user):
    await make_user(email="tech@example.com", password="techpass1", role="technician")
    login = await anon_client.post(
        "/api/v1/auth/login",
        json={"email": "tech@example.com", "password": "techpass1"},
    )
    token = login.json()["access_token"]

    resp = await anon_client.post(
        "/api/v1/auth/users",
        json={"email": "new@example.com", "password": "newpass123"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_admin_can_create_user(anon_client, make_user):
    await make_user(email="admin@example.com", password="adminpass1", role="admin")
    login = await anon_client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "adminpass1"},
    )
    token = login.json()["access_token"]

    resp = await anon_client.post(
        "/api/v1/auth/users",
        json={"email": "new@example.com", "password": "newpass123", "role": "pharmacist"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    assert resp.json()["email"] == "new@example.com"
