from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Optional
from app.shared.constants.roles import OrderStatus
from app.shared.utils.weight_converter import weight_summary


@dataclass
class OrderItem:
    id: int
    pedido_id: int
    producto_id: int
    cantidad_kg: Decimal                        # cantidad en kilogramos
    precio_unitario_kg: Decimal                 # precio VENTA snapshot
    precio_compra_unitario_kg: Decimal = Decimal("0")  # precio COMPRA snapshot
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @property
    def subtotal(self) -> Decimal:
        return self.cantidad_kg * self.precio_unitario_kg

    @property
    def cantidad_all_units(self) -> dict:
        return weight_summary(self.cantidad_kg)


@dataclass
class Order:
    # ── Campos obligatorios (sin default) ─────────────────────────────────────
    id: int
    nombre_cliente: str
    documento_cliente: str
    lugar: str
    fecha_hora: datetime
    precio_total: Decimal
    # ── Campos opcionales (con default) ───────────────────────────────────────
    id_domiciliario: Optional[int] = None       # SET NULL si se elimina el usuario
    nombre_domiciliario: Optional[str] = None   # snapshot del nombre al crear
    id_vehiculo: Optional[int] = None
    estado: OrderStatus = OrderStatus.PENDIENTE
    items: list[OrderItem] = field(default_factory=list)
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
        return self.estado in (OrderStatus.PENDIENTE, OrderStatus.EN_PROCESO)

    @property
    def total_kg(self) -> Decimal:
        return sum(item.cantidad_kg for item in self.items)

    @property
    def total_all_units(self) -> dict:
        return weight_summary(self.total_kg)
