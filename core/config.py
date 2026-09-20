from pydantic_settings import BaseSettings
from typing import Optional, List


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
    # Asegúrate de configurar SECRET_KEY en producción a través del archivo .env
    SECRET_KEY: str = "super_secret_key_change_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 días por defecto
    BACKEND_CORS_ORIGINS: List[str] = ["*"]  # Lista de orígenes permitidos para CORS

    # ─── FIRST ADMIN (seed) ───────────────────────────────
    FIRST_ADMIN_EMAIL: str = "admin@fashionstore.com"
    # Asegúrate de configurar FIRST_ADMIN_PASSWORD en el archivo .env
    FIRST_ADMIN_PASSWORD: str = "Admin@1234"
    FIRST_ADMIN_NAME: str = "Administrador Principal"

    # ─── GOOGLE GEMINI AI ─────────────────────────────────
    # Configuracion IA (Gemini)
    GEMINI_API_KEY_1: str = ""
    GEMINI_API_KEY_2: str = ""
    GEMINI_API_KEY_3: str = ""
    GEMINI_API_KEY_4: str = ""
    GEMINI_MODEL: str = "gemini-3.1-flash-image"
    AI_TRYON_ENABLED: bool = True
    TRYON_UPLOAD_DIR: str = "uploads/tryon"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()
