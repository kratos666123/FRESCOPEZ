from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional
from app.shared.utils.weight_converter import weight_summary


@dataclass
class Product:
    id: int
    categoria_id: int
    nombre: str
    precio: Decimal              # precio VENTA por kg
    precio_compra_kg: Decimal    # precio COMPRA por kg
    stock_kg: Decimal            # stock almacenado en kilogramos
    activo: bool = True
    descripcion: Optional[str] = None
    imagen: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    created_by: Optional[int] = None
    updated_by: Optional[int] = None

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    @property
    def stock_all_units(self) -> dict:
        """Stock disponible en todas las unidades."""
        return weight_summary(self.stock_kg)

    def has_sufficient_stock(self, quantity_kg: Decimal) -> bool:
        return self.stock_kg >= quantity_kg

    def reduce_stock(self, quantity_kg: Decimal) -> None:
        self.stock_kg -= quantity_kg

    def increase_stock(self, quantity_kg: Decimal) -> None:
        self.stock_kg += quantity_kg
