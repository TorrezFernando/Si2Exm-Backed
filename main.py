"""
FashionStore API — Punto de entrada principal
=============================================
Ejecutar en desarrollo:
    .\\venv\\Scripts\\uvicorn main:app --reload

Documentación interactiva (Swagger):
    http://localhost:8000/api/v1/openapi.json  →  http://localhost:8000/docs
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from core.config import settings
from db.database import engine, Base
# Importar todos los modelos para que Alembic y Base los reconozcan
from db.models import *  # noqa: F401,F403


# ─── Lifespan: Inicialización y cierre de la app ─────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Evento de inicio: verifica conexión a la BD.
    En producción las migraciones se aplican con Alembic (no create_all).
    """
    print(f"[START] Iniciando {settings.PROJECT_NAME} v{settings.VERSION}")
    print(f"[DB]    Base de datos: {settings.SQLALCHEMY_DATABASE_URI[:50]}...")
    yield
    print("[STOP] Cerrando la aplicacion.")


# ─── Instancia FastAPI ────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "API REST para FashionStore — plataforma de e-commerce de ropa "
        "con catálogo, reservas, ventas presenciales, IA y AR."
    ),
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ─── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # ⚠️ Ajustar a dominios específicos en producción
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Health Check ─────────────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
def root():
    """Endpoint de verificación de salud de la API."""
    return {
        "status": "ok",
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
    }


# ─── Routers (CU = Caso de Uso) ───────────────────────────────────────────────
from api.routers import auth, users

# CU-01, CU-02: Registro y Login
app.include_router(
    auth.router,
    prefix=f"{settings.API_V1_STR}/auth",
    tags=["🔐 Autenticación"],
)

# CU-03: Gestión de Usuarios y Roles (Admin)
app.include_router(
    users.router,
    prefix=f"{settings.API_V1_STR}/users",
    tags=["👥 Usuarios y Roles"],
)
