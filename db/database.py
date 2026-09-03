from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from core.config import settings

# ─── Motor de Base de Datos ────────────────────────────────────────────────────
# Si la URL es SQLite (desarrollo local sin PostgreSQL), se agrega check_same_thread.
# En producción con PostgreSQL este bloque simplemente usa create_engine normal.
if settings.SQLALCHEMY_DATABASE_URI.startswith("sqlite"):
    engine = create_engine(
        settings.SQLALCHEMY_DATABASE_URI,
        connect_args={"check_same_thread": False},
    )
else:
    # PostgreSQL en producción: pool optimizado
    engine = create_engine(
        settings.SQLALCHEMY_DATABASE_URI,
        pool_pre_ping=True,   # Verifica que la conexión esté viva antes de usarla
        pool_size=10,
        max_overflow=20,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency de FastAPI que provee una sesión de BD y la cierra al terminar."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
