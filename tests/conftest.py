import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database.db_connection import close_db, get_db, init_db
from app.database.seed import seed_database

@pytest_asyncio.fixture
async def client():
    await init_db()
    await seed_database(await get_db())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    await close_db()

@pytest.fixture
def doctor_payload():
    return {"email": "doctor@sepsis.ai", "password": "Doctor@123"}

@pytest.fixture
def nurse_payload():
    return {"email": "nurse@sepsis.ai", "password": "Nurse@123"}
