from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Optional
from app.shared.constants.roles import DeliveryType, DeliveryStatus
from app.shared.utils.weight_converter import weight_summary


@dataclass
class DeliveryItem:
    id: int
    entrega_id: int
    producto_id: int
    cantidad_kg: Decimal                  # cantidad en kilogramos
    precio_compra_unitario_kg: Decimal = Decimal("0")  # precio compra snapshot al momento
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @property
    def subtotal_compra(self) -> Decimal:
        return self.cantidad_kg * self.precio_compra_unitario_kg

    @property
    def cantidad_all_units(self) -> dict:
        return weight_summary(self.cantidad_kg)


@dataclass
class Delivery:
    id: int
    tipo: DeliveryType
    fecha_hora: datetime
    estado: DeliveryStatus = DeliveryStatus.PENDIENTE
    id_domiciliario: Optional[int] = None
    nombre_domiciliario: Optional[str] = None  # snapshot
    id_vehiculo: Optional[int] = None
    items: list[DeliveryItem] = field(default_factory=list)
    observaciones: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    @property
    def is_cancellable(self) -> bool:
        return self.estado in (DeliveryStatus.PENDIENTE, DeliveryStatus.EN_PROCESO)

    @property
    def is_completable(self) -> bool:
        return self.estado == DeliveryStatus.EN_PROCESO

    @property
    def total_kg(self) -> Decimal:
        return sum(item.cantidad_kg for item in self.items)

    @property
    def total_all_units(self) -> dict:
        return weight_summary(self.total_kg)
