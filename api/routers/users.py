"""
Router: Gestión de Usuarios y Roles (Admin)
=============================================
CU-03: El administrador puede crear, leer, actualizar y desactivar usuarios.
       También puede asignar roles y sucursales a empleados.

Endpoints disponibles (prefijo: /api/v1/users):
  GET    /               → Listar todos los usuarios (Admin)
  POST   /               → Crear nuevo usuario con rol específico (Admin)
  GET    /me             → Ver perfil propio (cualquier usuario autenticado)
  GET    /{user_id}      → Ver usuario por ID (Admin)
  PATCH  /{user_id}      → Actualizar usuario: nombre, rol, sucursal, estado (Admin)
  DELETE /{user_id}      → Desactivar usuario (soft delete) (Admin)
  POST   /{user_id}/activate   → Reactivar usuario (Admin)
  PATCH  /{user_id}/role       → Cambiar solo el rol de un usuario (Admin)
  POST   /change-password      → Cambiar contraseña propia (cualquier usuario)
"""
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from api.deps import (
    get_db,
    get_current_active_user,
    require_admin,
    require_admin_or_encargado,
)
from core import security
from db.models.user import User, RoleEnum
from db.models.branch import Branch
from schemas.user import (
    User as UserSchema,
    UserCreateByAdmin,
    UserUpdate,
    PasswordChange,
)

router = APIRouter()


# ─── LISTAR USUARIOS ──────────────────────────────────────────────────────────

@router.get("/", response_model=List[UserSchema])
def list_users(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
    skip: int = Query(0, ge=0, description="Número de registros a omitir (paginación)"),
    limit: int = Query(50, ge=1, le=200, description="Máximo de registros a devolver"),
    role: Optional[RoleEnum] = Query(None, description="Filtrar por rol específico"),
    branch_id: Optional[int] = Query(None, description="Filtrar por sucursal"),
    is_active: Optional[bool] = Query(None, description="Filtrar por estado activo/inactivo"),
) -> Any:
    """
    CU-03: Lista todos los usuarios del sistema con filtros opcionales.
    Solo accesible para el rol Admin.
    """
    query = db.query(User)

    if role is not None:
        query = query.filter(User.role == role)
    if branch_id is not None:
        query = query.filter(User.branch_id == branch_id)
    if is_active is not None:
        query = query.filter(User.is_active == is_active)

    return query.offset(skip).limit(limit).all()


# ─── CREAR USUARIO CON ROL (por Admin) ───────────────────────────────────────

@router.post("/", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
def create_user_by_admin(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
    user_in: UserCreateByAdmin,
) -> Any:
    """
    CU-03: El administrador crea un usuario con un rol específico.

    Reglas de negocio:
    - Si el rol es 'cajero' o 'encargado', se debe proporcionar un branch_id válido.
    - El correo electrónico debe ser único en el sistema.
    """
    # Verificar email único
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe un usuario con el correo: {user_in.email}",
        )

    # Validar que cajero/encargado tengan sucursal asignada
    if user_in.role in (RoleEnum.cajero, RoleEnum.encargado):
        if not user_in.branch_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"El rol '{user_in.role.value}' requiere asignar una sucursal (branch_id).",
            )
        # Verificar que la sucursal exista y esté activa
        branch = db.query(Branch).filter(
            Branch.id == user_in.branch_id,
            Branch.is_active == True,
        ).first()
        if not branch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sucursal con ID {user_in.branch_id} no encontrada o inactiva.",
            )

    # Crear el usuario
    new_user = User(
        email=user_in.email,
        hashed_password=security.get_password_hash(user_in.password),
        full_name=user_in.full_name,
        phone=user_in.phone,
        role=user_in.role,
        branch_id=user_in.branch_id,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


# ─── VER USUARIO POR ID ───────────────────────────────────────────────────────

@router.get("/{user_id}", response_model=UserSchema)
def get_user(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
    user_id: int,
) -> Any:
    """CU-03: Obtiene el detalle completo de un usuario por su ID."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    return user


# ─── ACTUALIZAR USUARIO (nombre, rol, sucursal, estado) ──────────────────────

@router.patch("/{user_id}", response_model=UserSchema)
def update_user(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
    user_id: int,
    user_in: UserUpdate,
) -> Any:
    """
    CU-03: Actualiza datos de un usuario.
    Permite cambiar nombre, teléfono, rol, sucursal y estado activo/inactivo.

    Si se cambia el rol a cajero/encargado, se valida que tenga branch_id.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    # Determinar el rol final (el nuevo si viene, el actual si no)
    final_role = user_in.role if user_in.role is not None else user.role
    final_branch = user_in.branch_id if user_in.branch_id is not None else user.branch_id

    # Validar sucursal para roles de empleado
    if final_role in (RoleEnum.cajero, RoleEnum.encargado) and not final_branch:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"El rol '{final_role.value}' requiere una sucursal asignada.",
        )

    # Validar que la sucursal exista si se proporciona
    if user_in.branch_id is not None:
        branch = db.query(Branch).filter(Branch.id == user_in.branch_id).first()
        if not branch:
            raise HTTPException(
                status_code=404,
                detail=f"Sucursal con ID {user_in.branch_id} no encontrada.",
            )

    # Aplicar cambios (solo los campos que no sean None)
    update_data = user_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return user


# ─── CAMBIAR SOLO EL ROL ─────────────────────────────────────────────────────

@router.patch("/{user_id}/role", response_model=UserSchema)
def change_user_role(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
    user_id: int,
    new_role: RoleEnum = Query(..., description="Nuevo rol a asignar"),
    branch_id: Optional[int] = Query(None, description="Sucursal (requerida para cajero/encargado)"),
) -> Any:
    """
    CU-03: Endpoint dedicado al cambio de rol de un usuario.
    Más conveniente que PATCH cuando solo se quiere cambiar el rol.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    # No se puede quitar el rol admin si es el único admin
    if user.role == RoleEnum.admin and new_role != RoleEnum.admin:
        admin_count = db.query(User).filter(
            User.role == RoleEnum.admin, User.is_active == True
        ).count()
        if admin_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se puede cambiar el rol del único administrador activo del sistema.",
            )

    if new_role in (RoleEnum.cajero, RoleEnum.encargado):
        bid = branch_id or user.branch_id
        if not bid:
            raise HTTPException(
                status_code=422,
                detail=f"Se requiere branch_id para asignar el rol '{new_role.value}'.",
            )
        branch = db.query(Branch).filter(Branch.id == bid).first()
        if not branch:
            raise HTTPException(status_code=404, detail="Sucursal no encontrada.")
        user.branch_id = bid

    user.role = new_role
    db.commit()
    db.refresh(user)
    return user


# ─── DESACTIVAR USUARIO (soft delete) ─────────────────────────────────────────

@router.delete("/{user_id}", response_model=UserSchema)
def deactivate_user(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
    user_id: int,
) -> Any:
    """
    CU-03: Desactiva un usuario (soft delete).
    No elimina el registro de la BD para preservar historial de reservas/ventas.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    if user.id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail="No puedes desactivar tu propia cuenta.",
        )

    # Proteger al último admin
    if user.role == RoleEnum.admin:
        admin_count = db.query(User).filter(
            User.role == RoleEnum.admin, User.is_active == True
        ).count()
        if admin_count <= 1:
            raise HTTPException(
                status_code=400,
                detail="No se puede desactivar al único administrador activo.",
            )

    user.is_active = False
    db.commit()
    db.refresh(user)
    return user


# ─── REACTIVAR USUARIO ────────────────────────────────────────────────────────

@router.post("/{user_id}/activate", response_model=UserSchema)
def activate_user(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
    user_id: int,
) -> Any:
    """CU-03: Reactiva un usuario previamente desactivado."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")

    user.is_active = True
    db.commit()
    db.refresh(user)
    return user


# ─── CAMBIAR CONTRASEÑA PROPIA ────────────────────────────────────────────────

@router.post("/change-password", status_code=status.HTTP_200_OK)
def change_own_password(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    password_data: PasswordChange,
) -> Any:
    """Permite a cualquier usuario autenticado cambiar su propia contraseña."""
    if not security.verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="La contraseña actual es incorrecta.")

    current_user.hashed_password = security.get_password_hash(password_data.new_password)
    db.commit()
    return {"message": "Contraseña actualizada exitosamente."}
