"""
Script para crear el usuario administrador inicial.
Ejecutar una sola vez después de las migraciones:
    python seed.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.infrastructure.database.session import SessionLocal, engine
from app.infrastructure.database.session import Base
from app.infrastructure.database.models.user_model import UserModel
from app.infrastructure.security.password_handler import hash_password
from app.shared.constants.roles import UserRole
from sqlalchemy import select


def seed():
    db = SessionLocal()
    try:
        # Check if admin already exists
        stmt = select(UserModel).where(UserModel.username == "admin", UserModel.deleted_at.is_(None))
        existing = db.execute(stmt).scalar_one_or_none()

        if existing:
            print("✅ El usuario administrador ya existe.")
            return

        admin = UserModel(
            username="admin",
            password_hash=hash_password("Admin1234!"),
            role=UserRole.ADMIN,
            nombre="Administrador Principal",
            correo="admin@empresa.com",
            telefono=None,
            documento="0000000001",
            is_active=True,
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)

        print("✅ Usuario administrador creado exitosamente:")
        print(f"   Usuario:    admin")
        print(f"   Contraseña: Admin1234!")
        print(f"   Rol:        {admin.role}")
        print(f"   ID:         {admin.id}")
        print()
        print("⚠️  CAMBIA LA CONTRASEÑA inmediatamente después del primer inicio de sesión.")

    finally:
        db.close()


if __name__ == "__main__":
    seed()
