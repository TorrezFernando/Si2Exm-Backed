from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    PROJECT_NAME: str = "FashionStore API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # ─── DATABASE ─────────────────────────────────────────
    # Leer la URL completa desde el .env (compatible con PostgreSQL y SQLite)
    DATABASE_URL: str = "sqlite:///./fashionstore.db"

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return self.DATABASE_URL

    # ─── SECURITY ─────────────────────────────────────────
    SECRET_KEY: str = "super_secret_key_change_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 días por defecto

    # ─── FIRST ADMIN (seed) ───────────────────────────────
    FIRST_ADMIN_EMAIL: str = "admin@fashionstore.com"
    FIRST_ADMIN_PASSWORD: str = "Admin@1234"
    FIRST_ADMIN_NAME: str = "Administrador Principal"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()
