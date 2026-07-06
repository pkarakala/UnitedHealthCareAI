import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_prior_auths_empty(client: AsyncClient):
    response = await client.get("/api/v1/prior-auths")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_prior_auth_not_found(client: AsyncClient):
    response = await client.get("/api/v1/prior-auths/nonexistent")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_cancel_prior_auth_not_found(client: AsyncClient):
    response = await client.post("/api/v1/prior-auths/nonexistent/cancel")
    assert response.status_code == 404
