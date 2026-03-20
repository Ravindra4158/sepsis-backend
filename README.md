# SepsisShield AI — Backend API

**Team-25 SPUTNIK SYNC** | NHH 2.0 | Leader: Ravindra

AI-Based Early Sepsis Detection System — FastAPI Backend

---

## Quick Start

### 1. Clone & setup
```bash
cd sepsis-backend
python -m venv venv
# Windows PowerShell activation:
.\\venv\\Scripts\\Activate.ps1
# Windows CMD activation:
venv\\Scripts\\activate.bat
# Unix/Linux/macOS activation:
source venv/bin/activate
pip install -r requirements.txt
copy .env.example .env
# edit .env as needed
```

### 2. Run locally
```bash
# Using MongoDB Atlas from .env:
uvicorn app.main:app --reload
```

### 3. Seed sample data
```bash
python scripts/seed_database.py
```

### 4. API Docs
- Swagger UI: http://localhost:8000/docs
- ReDoc:       http://localhost:8000/redoc

---

## Default Login Credentials (after seeding)

| Role   | Email               | Password     |
|--------|---------------------|--------------|
| Doctor | doctor@sepsis.ai    | Doctor@123   |
| Nurse  | nurse@sepsis.ai     | Nurse@123    |
| Admin  | admin@sepsis.ai     | Admin@123    |

---

## Project Structure

```
app/
├── main.py              FastAPI app + lifespan + routers
├── config/              Settings (pydantic-settings)
├── routes/              URL routing (6 modules)
├── controllers/         Request handlers + response shaping
├── services/            Business logic layer
├── schemas/             Pydantic request/response schemas
├── database/            Mongo connection + seed helpers
├── ml/                  ML prediction pipeline
├── middlewares/         Auth + logging middleware
├── utils/               JWT, hashing, validators, logger
└── websocket/           WebSocket connection manager
```

---

## Running Tests
```bash
python -m pytest tests/ -v
```

---

## WebSocket
Connect to `ws://localhost:8000/ws/alerts` for real-time alert push.
Send `{"type":"ping"}` to keep connection alive.
