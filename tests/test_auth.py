import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"

@pytest.mark.asyncio
async def test_register_and_login(client: AsyncClient):
    reg = await client.post("/api/v1/auth/register", json={
        "name": "Test Doctor", "email": "testdoc@test.com",
        "password": "TestDoc@123", "role": "doctor", "ward": "ICU-A"
    })
    assert reg.status_code in (201, 409)
    login = await client.post("/api/v1/auth/login", json={
        "email": "testdoc@test.com", "password": "TestDoc@123"
    })
    assert login.status_code == 200
    data = login.json()
    assert "access_token" in data
    assert data["user"]["role"] == "doctor"

@pytest.mark.asyncio
async def test_invalid_login(client: AsyncClient):
    r = await client.post("/api/v1/auth/login", json={"email": "bad@test.com", "password": "wrong"})
    assert r.status_code == 401

@pytest.mark.asyncio
async def test_protected_requires_token(client: AsyncClient):
    r = await client.get("/api/v1/patients/")
    assert r.status_code == 403
