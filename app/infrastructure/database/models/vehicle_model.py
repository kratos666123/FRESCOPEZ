from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, Boolean, DateTime, Integer, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column
from app.infrastructure.database.session import Base


class VehicleModel(Base):
    __tablename__ = "vehicles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    placa: Mapped[str] = mapped_column(String(20), nullable=False, unique=True, index=True)
    color: Mapped[str] = mapped_column(String(50), nullable=False)
    tipo_vehiculo: Mapped[str] = mapped_column(String(100), nullable=False)
    capacidad_kg: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    carga_actual_kg: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False, default=Decimal("0"))
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    created_by: Mapped[int | None] = mapped_column(Integer, nullable=True)
    updated_by: Mapped[int | None] = mapped_column(Integer, nullable=True)

    def __repr__(self) -> str:
        return f"<VehicleModel placa={self.placa} capacidad={self.capacidad_kg}kg carga={self.carga_actual_kg}kg>"
