from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.config.settings import settings
from app.database.db_connection import close_db, get_db, init_db
from app.database.seed import seed_database
from app.middlewares.logging_middleware import LoggingMiddleware
from app.ml.model_loader import load_model
from app.routes import auth_routes, patient_routes, vitals_routes, prediction_routes, alert_routes, user_routes, admin_routes, labs_routes
from app.websocket.alert_socket import alert_websocket_endpoint
from app.utils.logger import logger

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting SepsisShield AI Backend...")
    await init_db()
    await seed_database(await get_db())
    load_model()
    logger.info(f"✅ Server ready on {settings.HOST}:{settings.PORT}")
    yield
    await close_db()
    logger.info("🛑 Shutting down SepsisShield AI Backend")

app = FastAPI(
    title="SepsisShield AI",
    description=(
        "AI-Based Early Sepsis Detection System API\n\n"
        "**Team-25 SPUTNIK SYNC** | NHH 2.0 | Leader: Ravindra\n\n"
        "Provides real-time sepsis risk prediction, alert management, "
        "patient monitoring, and role-based clinical workflows."
    ),
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# ── Middleware ────────────────────────────────────────────────────────
app.add_middleware(LoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────
API_PREFIX = "/api/v1"
app.include_router(auth_routes.router,       prefix=API_PREFIX)
app.include_router(patient_routes.router,    prefix=API_PREFIX)
app.include_router(vitals_routes.router,     prefix=API_PREFIX)
app.include_router(prediction_routes.router, prefix=API_PREFIX)
app.include_router(alert_routes.router,      prefix=API_PREFIX)
app.include_router(user_routes.router,       prefix=API_PREFIX)
app.include_router(admin_routes.router,      prefix=API_PREFIX)
app.include_router(labs_routes.router,       prefix=API_PREFIX)

# ── WebSocket ─────────────────────────────────────────────────────────
@app.websocket("/ws/alerts")
async def ws_all(websocket: WebSocket):
    await alert_websocket_endpoint(websocket, ward="all")

@app.websocket("/ws/alerts/{ward}")
async def ws_ward(websocket: WebSocket, ward: str):
    await alert_websocket_endpoint(websocket, ward=ward)

# ── Health ────────────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
async def root():
    return {"app": settings.APP_NAME, "version": settings.APP_VERSION, "status": "running", "docs": "/docs"}

@app.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy", "environment": settings.ENVIRONMENT}
