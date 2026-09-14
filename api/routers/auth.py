from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session, joinedload

from api import deps
from api.audit_logger import log_audit
from core import security
from core.config import settings
from db.models.user import User
from db.models.rbac import Role
from schemas.user import User as UserSchema, UserCreate, Token

router = APIRouter()


@router.post("/login", response_model=Token)
def login_access_token(
    db: Session = Depends(deps.get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Any:
    user = db.query(User).options(joinedload(User.role)).filter(User.email == form_data.username).first()
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo. Contacta al administrador.",
        )

    role_name = user.role.name if user.role else None

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        subject=user.id, role=role_name, expires_delta=access_token_expires
    )
    
    log_audit(db, user.id, "LOGIN", "AUTH", str(user.id), None)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": role_name,
    }


@router.post("/register", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
def register_user(
    *,
    db: Session = Depends(deps.get_db),
    user_in: UserCreate,
) -> Any:
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe una cuenta con ese correo electrónico.",
        )
        
    cliente_role = db.query(Role).filter(Role.name == "cliente").first()
    if not cliente_role:
        raise HTTPException(status_code=500, detail="Rol 'cliente' no configurado en BD.")
        
    user = User(
        email=user_in.email,
        hashed_password=security.get_password_hash(user_in.password),
        full_name=user_in.full_name,
        phone=user_in.phone,
        role_id=cliente_role.id
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    log_audit(db, user.id, "REGISTER", "AUTH", str(user.id), None)
    
    return user


@router.get("/me", response_model=UserSchema)
def read_users_me(
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    return current_user
