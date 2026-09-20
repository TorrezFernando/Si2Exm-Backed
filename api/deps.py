from typing import Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload

from core.config import settings
from db.database import SessionLocal
from db.models.user import User
from db.models.rbac import Role, Permission, UserPermission
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
    Valida el JWT y devuelve el usuario autenticado (con su rol cargado).
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
    # Cargar usuario con su rol asociado usando joinedload para evitar N+1
    user = db.query(User).options(joinedload(User.role)).filter(User.id == int(token_data.sub)).first()
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

oauth2_scheme_optional = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login", 
    auto_error=False
)

def get_current_user_optional(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme_optional),
) -> User | None:
    if not token:
        return None
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
    except (JWTError, ValidationError):
        return None
    user = db.query(User).options(joinedload(User.role)).filter(User.id == int(token_data.sub)).first()
    return user

def get_user_permissions(db: Session, user: User) -> set[str]:
    """Obtiene el set de permisos (strings) de un usuario (Rol + UserPermissions)."""
    permissions = set()
    
    # 1. Permisos del rol
    if user.role:
        for perm in user.role.permissions:
            permissions.add(perm.name)
            
    # 2. Permisos específicos del usuario (override)
    user_perms = db.query(UserPermission).options(joinedload(UserPermission.permission)).filter(UserPermission.user_id == user.id).all()
    for up in user_perms:
        if up.is_granted:
            permissions.add(up.permission.name)
        else:
            if up.permission.name in permissions:
                permissions.remove(up.permission.name)
                
    return permissions

# ─── Dependencies de Autorización por Permiso (RBAC) ──────────────────────────

def require_permission(*required_perms: str):
    """
    Factory de dependency que restringe el acceso a usuarios con un permiso específico.
    Si se pasan varios, el usuario debe tener AL MENOS UNO de ellos (OR).
    """
    def permission_checker(
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ) -> User:
        user_perms = get_user_permissions(db, current_user)
        
        # El admin siempre tiene todos los permisos en seed.py, pero 
        # también podemos hardcodear que si role.name == 'admin', pasa todo.
        # Por seguridad y completitud, el rol admin tiene asignados los permisos en BD.
        
        has_access = any(req_perm in user_perms for req_perm in required_perms)
        
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acceso denegado. Se requiere alguno de estos permisos: {required_perms}",
            )
        return current_user
    return permission_checker


# Shortcuts comunes basados en permisos
require_admin_role = require_permission("roles:manage") # Solo admins manejan roles
require_staff = require_permission("inventory:read", "sales:write")
