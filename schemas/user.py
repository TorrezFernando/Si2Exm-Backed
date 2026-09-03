from pydantic import BaseModel, EmailStr
from typing import Optional
from enum import Enum
from datetime import datetime


class RoleEnum(str, Enum):
    """Espejo del enum de SQLAlchemy para validación Pydantic."""
    admin = "admin"
    encargado = "encargado"
    cajero = "cajero"
    cliente = "cliente"


# ─── Schemas base ─────────────────────────────────────────────────────────────

class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    phone: Optional[str] = None


# ─── Registro público (CU-01) ─────────────────────────────────────────────────

class UserCreate(UserBase):
    """Schema para el registro público de un nuevo cliente."""
    password: str


# ─── Creación de usuario por Admin (CU-03) ────────────────────────────────────

class UserCreateByAdmin(UserBase):
    """
    Schema que usa el Admin para crear cualquier tipo de usuario (empleados).
    Permite especificar rol y la sucursal a la que pertenece (para cajero/encargado).
    """
    password: str
    role: RoleEnum = RoleEnum.cliente
    branch_id: Optional[int] = None  # Obligatorio si role == cajero o encargado


# ─── Actualización de usuario (CU-03) ────────────────────────────────────────

class UserUpdate(BaseModel):
    """
    Schema para actualizar datos de un usuario existente.
    Todos los campos son opcionales para admitir actualizaciones parciales (PATCH).
    """
    full_name: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[RoleEnum] = None
    branch_id: Optional[int] = None  # Permite reasignar sucursal
    is_active: Optional[bool] = None


# ─── Cambio de contraseña ─────────────────────────────────────────────────────

class PasswordChange(BaseModel):
    current_password: str
    new_password: str


# ─── Schema de respuesta (sin contraseña) ────────────────────────────────────

class UserInDBBase(UserBase):
    id: int
    role: RoleEnum
    branch_id: Optional[int] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class User(UserInDBBase):
    """Schema de respuesta público (sin hashed_password)."""
    pass


class UserInDB(UserInDBBase):
    """Schema interno con contraseña hasheada (solo para uso interno)."""
    hashed_password: str


# ─── Schemas de Token JWT ─────────────────────────────────────────────────────

class Token(BaseModel):
    access_token: str
    token_type: str
    role: str       # Devolvemos el rol en el login para que el frontend redirija


class TokenPayload(BaseModel):
    sub: Optional[str] = None   # user_id como string
    role: Optional[str] = None
