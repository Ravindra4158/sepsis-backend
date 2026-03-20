import pytest
from httpx import AsyncClient

async def get_token(client, email, password):
    r = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return r.json().get("access_token", "")

@pytest.mark.asyncio
async def test_patient_lifecycle(client: AsyncClient):
    token = await get_token(client, "testdoc@test.com", "TestDoc@123")
    headers = {"Authorization": f"Bearer {token}"}
    create_r = await client.post("/api/v1/patients/", headers=headers, json={
        "mrn": "TEST-999", "first_name": "Test", "last_name": "Patient",
        "date_of_birth": "1980-01-01", "gender": "M",
        "ward": "ICU-A", "bed_number": 99,
    })
    assert create_r.status_code in (201, 409)
    list_r = await client.get("/api/v1/patients/", headers=headers)
    assert list_r.status_code == 200
    assert "patients" in list_r.json()

@pytest.mark.asyncio
async def test_search_patients(client: AsyncClient):
    token = await get_token(client, "testdoc@test.com", "TestDoc@123")
    r = await client.get("/api/v1/patients/search?q=Test", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert isinstance(r.json(), list)
