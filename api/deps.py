from typing import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError
from sqlalchemy.orm import Session

from core.config import settings
from db.database import SessionLocal
from db.models.user import User, RoleEnum
from schemas.user import TokenPayload

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)


def get_db() -> Generator:
    """Dependency que provee una sesión de BD por request."""
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
) -> User:
    """
    Valida el JWT y devuelve el usuario autenticado.
    Lanza 403 si el token es inválido o expirado.
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No se pudo validar las credenciales. Token inválido o expirado.",
        )
    user = db.query(User).filter(User.id == int(token_data.sub)).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Valida que el usuario esté activo."""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Usuario inactivo.")
    return current_user


# ─── Dependencies de Autorización por Rol ─────────────────────────────────────

def require_role(*roles: RoleEnum):
    """
    Factory de dependency que restringe el acceso a usuarios con roles específicos.

    Uso:
        @router.get("/admin-only")
        def admin_endpoint(user = Depends(require_role(RoleEnum.admin))):
            ...
    """
    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acceso denegado. Se requiere uno de los roles: {[r.value for r in roles]}",
            )
        return current_user
    return role_checker


# Shortcuts para los roles más usados
require_admin = require_role(RoleEnum.admin)
require_admin_or_encargado = require_role(RoleEnum.admin, RoleEnum.encargado)
require_admin_or_cajero = require_role(RoleEnum.admin, RoleEnum.cajero)
require_staff = require_role(RoleEnum.admin, RoleEnum.encargado, RoleEnum.cajero)
