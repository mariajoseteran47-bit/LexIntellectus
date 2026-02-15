"""
LexIntellectus ERP - Main Application Entry Point
FastAPI application with CORS, route registration, and startup events.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db
from app.api.v1 import health, auth, users, tenants, cases, deadlines, documents, notifications, dashboard, ai_agent
from app.middleware.tenant import TenantMiddleware
from app.middleware.request_logger import RequestLoggerMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — runs on startup and shutdown."""
    # Startup: create tables if they don't exist (dev only)
    if settings.APP_ENV == "development":
        await init_db()
        print(f"🏛️  {settings.APP_NAME} v{settings.APP_VERSION} starting...")
        print(f"📊 Database: {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}")
        print(f"🔄 Redis: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
        print(f"📦 MinIO: {settings.MINIO_ENDPOINT}")
    yield
    # Shutdown
    print(f"🛑 {settings.APP_NAME} shutting down...")


app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "ERP SaaS para el sector legal nicaragüense. "
        "Gestión procesal, notarial, financiera y asistente legal con IA."
    ),
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# === Middleware ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Custom Middleware ===
app.add_middleware(TenantMiddleware)
app.add_middleware(RequestLoggerMiddleware)

# === Routes ===
api_prefix = settings.API_V1_PREFIX

app.include_router(auth.router, prefix=api_prefix)
app.include_router(users.router, prefix=api_prefix)
app.include_router(tenants.router, prefix="/api/v1/tenants", tags=["Tenants"])
app.include_router(cases.router, prefix="/api/v1/cases", tags=["Cases"])
app.include_router(deadlines.router, prefix="/api/v1/deadlines", tags=["Deadlines"])
app.include_router(documents.router, prefix="/api/v1/documents", tags=["Documents"])
app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["Notifications"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["Dashboard"])
app.include_router(ai_agent.router, prefix="/api/v1/ai", tags=["Legal AI Agent"])
app.include_router(health.router, prefix=api_prefix)

@app.get("/")
async def root():
    """Root endpoint — API welcome message."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": "ERP Legal SaaS para Nicaragua",
        "docs": "/docs",
        "api": f"{api_prefix}/health",
    }
