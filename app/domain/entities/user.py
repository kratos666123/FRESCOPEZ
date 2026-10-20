from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from app.shared.constants.roles import UserRole


@dataclass
class User:
    id: int
    username: str
    password_hash: str
    role: UserRole
    nombre: str
    correo: str
    documento: str
    is_active: bool = True
    telefono: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None

    @property
    def is_admin(self) -> bool:
        return self.role == UserRole.ADMIN

    @property
    def is_repartidor(self) -> bool:
        return self.role == UserRole.REPARTIDOR

    @property
    def is_empleado(self) -> bool:
        return self.role == UserRole.EMPLEADO

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None
