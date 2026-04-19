"""
LexIntellectus ERP - Main Application Entry Point
FastAPI application with CORS, route registration, and startup events.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db
from app.api.v1 import health, auth, users, tenants, cases, deadlines, documents, notifications, dashboard, ai_agent, audit, case_timeline, reports, client_profiles, professional_profiles, evidences
from app.middleware.tenant import TenantMiddleware
from app.middleware.request_logger import RequestLoggerMiddleware
from app.core.error_handlers import register_exception_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — runs on startup and shutdown."""
    # Startup: create tables if they don't exist (dev only)
    if settings.APP_ENV == "development":
        # await init_db()  # Redundant if using rebuild scripts, can cause issues with existing types
        print(f"🏛️  {settings.APP_NAME} v{settings.APP_VERSION} starting...")
        print(f"📊 Database: {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}")
        print(f"🔄 Redis: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
        print(f"📦 MinIO: {settings.MINIO_ENDPOINT}")
    yield
    # Shutdown
    print(f"🛑 {settings.APP_NAME} shutting down...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
## LexIntellectus ERP — API Legal SaaS para Nicaragua

Sistema integral de gestión jurídica con inteligencia artificial integrada.

### Módulos principales:
- **🏛️ Expedientes** — CRUD completo de casos judiciales
- **⏰ Plazos Fatales** — Gestión de términos procesales con alertas
- **📄 Documentos** — Almacenamiento seguro con validación
- **🤖 Asistente IA** — 4 modos: Consultor, Estratega, Redactor, Notario
- **👥 Usuarios** — Multi-tenant con RBAC
- **🛡️ Auditoría** — Registro completo de acciones del sistema
- **📊 Dashboard** — Estadísticas y reportes

### Autenticación:
Utiliza JWT Bearer Tokens. Obtén un token via `POST /auth/login`.
    """,
    contact={
        "name": "LexIntellectus Team",
        "email": "soporte@lexintellectus.com",
    },
    license_info={
        "name": "Propietario",
        "url": "https://lexintellectus.com/licencia",
    },
    openapi_tags=[
        {"name": "Health", "description": "Verificación de conectividad del sistema"},
        {"name": "Auth", "description": "Autenticación y gestión de tokens JWT"},
        {"name": "Users", "description": "Gestión de usuarios del despacho"},
        {"name": "Tenants", "description": "Gestión multi-tenant de despachos"},
        {"name": "Cases", "description": "Expedientes judiciales — CRUD y workflow de estados"},
        {"name": "Deadlines", "description": "Plazos fatales y términos procesales"},
        {"name": "Documents", "description": "Gestión documental con almacenamiento MinIO"},
        {"name": "Dashboard", "description": "Estadísticas y métricas del despacho"},
        {"name": "Legal AI Agent", "description": "Asistente de inteligencia artificial legal"},
        {"name": "Audit", "description": "Registro de auditoría de acciones del sistema"},
        {"name": "Notifications", "description": "Sistema de notificaciones y alertas"},
    ],
    lifespan=lifespan,
)

# === Error Handlers ===
register_exception_handlers(app)

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
app.include_router(tenants.router, prefix=api_prefix, tags=["Tenants"])
app.include_router(cases.router, prefix=api_prefix, tags=["Cases"])
app.include_router(deadlines.router, prefix=api_prefix, tags=["Deadlines"])
app.include_router(documents.router, prefix=api_prefix, tags=["Documents"])
app.include_router(notifications.router, prefix=api_prefix, tags=["Notifications"])
app.include_router(dashboard.router, prefix=api_prefix, tags=["Dashboard"])
app.include_router(ai_agent.router, prefix=api_prefix, tags=["Legal AI Agent"])
app.include_router(audit.router, prefix=api_prefix, tags=["Audit"])
app.include_router(case_timeline.router, prefix=api_prefix, tags=["Case Timeline"])
app.include_router(reports.router, prefix=api_prefix, tags=["Reports"])
app.include_router(client_profiles.router, prefix=api_prefix, tags=["Client Profiles"])
app.include_router(professional_profiles.router, prefix=api_prefix, tags=["Professional Profiles"])
app.include_router(evidences.router, prefix=api_prefix, tags=["Evidence Management"])
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
