import enum
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.database import Base


class RoleEnum(str, enum.Enum):
    """
    Roles del sistema FashionStore:
    - admin      : Acceso total. Gestiona usuarios, sucursales, catálogo y reportes.
    - encargado  : Gestor de una sucursal específica. Administra reservas e inventario local.
    - cajero     : Empleado de caja en una sucursal. Registra ventas presenciales.
    - cliente    : Usuario final que navega el catálogo, reserva y compra.
    """
    admin = "admin"
    encargado = "encargado"
    cajero = "cajero"
    cliente = "cliente"


class User(Base):
    """
    CU-01 / CU-02 / CU-03: Registro, Login y Gestión de Usuarios/Roles.

    Campos adicionales respecto al diseño anterior:
    - branch_id : FK opcional a Branch. Se asigna cuando el rol es 'encargado' o 'cajero'
                  para vincular al empleado con su sucursal de trabajo.
    - phone     : Teléfono de contacto (útil para notificaciones de reservas).
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    phone = Column(String, nullable=True)

    # Rol del usuario dentro del sistema
    role = Column(Enum(RoleEnum), default=RoleEnum.cliente, nullable=False)

    # Sucursal asignada (solo relevante para cajero/encargado)
    branch_id = Column(Integer, ForeignKey("branches.id"), nullable=True)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relación con Branch (lazy=True para no cargar siempre)
    branch = relationship("Branch", foreign_keys=[branch_id])
