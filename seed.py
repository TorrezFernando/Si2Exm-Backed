"""
Script de Seed: Inicializacion de datos basicos
=================================================
Ejecutar con:
    python seed.py

Crea:
  1. El primer usuario Administrador (si no existe).
  2. Sucursales de ejemplo (si no existen).

Este script es idempotente: puede ejecutarse multiples veces sin duplicar datos.
"""
import sys
import os

# Aseguramos que el directorio raiz este en el path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db.database import SessionLocal, engine, Base
from db.models import *  # noqa: F401,F403  - importa todos los modelos
from db.models.user import User, RoleEnum
from db.models.branch import Branch
from core.config import settings
from core import security


def seed():
    sep = "=" * 60
    print(sep)
    print("  FashionStore -- Inicializacion de Base de Datos")
    print(sep)

    # Crear todas las tablas si no existen
    Base.metadata.create_all(bind=engine)
    print("[OK] Tablas verificadas / creadas.\n")

    db = SessionLocal()

    try:
        # -- 1. Crear Admin Principal -------------------------------------------
        existing_admin = db.query(User).filter(
            User.email == settings.FIRST_ADMIN_EMAIL
        ).first()

        if existing_admin:
            print(f"[INFO] Admin ya existe: {settings.FIRST_ADMIN_EMAIL} -- omitiendo.")
        else:
            admin = User(
                email=settings.FIRST_ADMIN_EMAIL,
                hashed_password=security.get_password_hash(settings.FIRST_ADMIN_PASSWORD),
                full_name=settings.FIRST_ADMIN_NAME,
                role=RoleEnum.admin,
                is_active=True,
            )
            db.add(admin)
            db.commit()
            db.refresh(admin)
            print("[OK] Admin creado:")
            print(f"   Email    : {admin.email}")
            print(f"   Password : {settings.FIRST_ADMIN_PASSWORD}  (solo para dev)")
            print(f"   Rol      : {admin.role.value}\n")

        # -- 2. Crear Sucursales de Ejemplo ------------------------------------
        sample_branches = [
            {"name": "Sucursal Centro",    "address": "Av. Principal 100, Centro",    "phone": "591-70000001"},
            {"name": "Sucursal Norte",     "address": "Calle Norte 250, Zona Norte",  "phone": "591-70000002"},
            {"name": "Sucursal Sur (Mall)","address": "Mall Sur, Local 42, Zona Sur", "phone": "591-70000003"},
        ]

        for branch_data in sample_branches:
            existing = db.query(Branch).filter(Branch.name == branch_data["name"]).first()
            if existing:
                print(f"[INFO] Sucursal ya existe: {branch_data['name']} -- omitiendo.")
            else:
                branch = Branch(**branch_data)
                db.add(branch)
                db.commit()
                print(f"[OK] Sucursal creada: {branch_data['name']}")

        print()
        print(sep)
        print("  Seed completado exitosamente!")
        print(sep)

    except Exception as e:
        db.rollback()
        print(f"\n[ERROR] Error durante el seed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
