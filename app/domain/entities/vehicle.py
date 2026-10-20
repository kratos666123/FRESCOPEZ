from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional
from app.shared.utils.weight_converter import weight_summary


@dataclass
class Vehicle:
    id: int
    placa: str
    color: str
    tipo_vehiculo: str
    capacidad_kg: Decimal          # Capacidad máxima en kg
    carga_actual_kg: Decimal = Decimal("0")   # Carga actualmente asignada (kg)
    activo: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    @property
    def capacidad_disponible_kg(self) -> Decimal:
        """Capacidad libre restante."""
        return max(Decimal("0"), self.capacidad_kg - self.carga_actual_kg)

    def tiene_capacidad(self, peso_kg: Decimal) -> bool:
        """Verifica si hay capacidad suficiente para añadir peso_kg."""
        return self.capacidad_disponible_kg >= peso_kg

    @property
    def capacidad_all_units(self) -> dict:
        return weight_summary(self.capacidad_kg)

    @property
    def carga_actual_all_units(self) -> dict:
        return weight_summary(self.carga_actual_kg)

    @property
    def disponible_all_units(self) -> dict:
        return weight_summary(self.capacidad_disponible_kg)
