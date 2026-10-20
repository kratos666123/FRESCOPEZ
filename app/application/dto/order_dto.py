from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, model_validator
from app.shared.constants.roles import OrderStatus
from app.shared.utils.weight_converter import weight_summary
from app.application.dto.product_dto import StockWeightResponse


class OrderItemRequest(BaseModel):
    id_producto: int = Field(..., gt=0, examples=[1])
    cantidad_kg: Decimal = Field(..., gt=0, decimal_places=6, examples=[["25.500000"]])

    model_config = {"str_strip_whitespace": True}


class CreateOrderRequest(BaseModel):
    nombre_cliente: str = Field(..., min_length=2, max_length=200, examples=["Restaurante El Pescador"])
    documento_cliente: str = Field(..., min_length=5, max_length=50, examples=["9001234567"])
    id_domiciliario: int = Field(..., gt=0, examples=[3])
    id_vehiculo: int = Field(..., gt=0, description="Vehículo asignado (obligatorio)")
    lugar: str = Field(..., min_length=3, max_length=300, examples=["Carrera 7 #45-12, Bogotá"])
    fecha_hora: datetime = Field(..., examples=["2025-06-15T14:30:00"])
    items: list[OrderItemRequest] = Field(..., min_length=1)

    model_config = {"str_strip_whitespace": True}


class UpdateOrderRequest(BaseModel):
    nombre_cliente: Optional[str] = Field(None, min_length=2, max_length=200)
    documento_cliente: Optional[str] = Field(None, min_length=5, max_length=50)
    id_domiciliario: Optional[int] = Field(None, gt=0)
    id_vehiculo: Optional[int] = Field(None, gt=0)
    lugar: Optional[str] = Field(None, min_length=3, max_length=300)
    fecha_hora: Optional[datetime] = None
    estado: Optional[OrderStatus] = None
    items: Optional[list[OrderItemRequest]] = Field(None, min_length=1)

    model_config = {"str_strip_whitespace": True}


class OrderItemResponse(BaseModel):
    id: int
    producto_id: int
    cantidad_kg: Decimal
    cantidad: Optional[StockWeightResponse] = None
    precio_unitario_kg: Decimal
    precio_compra_unitario_kg: Decimal = Decimal("0")
    subtotal: Decimal

    model_config = {"from_attributes": True}

    @model_validator(mode="after")
    def compute_units(self) -> "OrderItemResponse":
        summary = weight_summary(self.cantidad_kg)
        self.cantidad = StockWeightResponse(**summary)
        self.subtotal = self.cantidad_kg * self.precio_unitario_kg
        return self


class OrderResponse(BaseModel):
    id: int
    nombre_cliente: str
    documento_cliente: str
    id_domiciliario: Optional[int] = None
    nombre_domiciliario: Optional[str] = None
    id_vehiculo: Optional[int] = None
    lugar: str
    fecha_hora: datetime
    precio_total: Decimal
    estado: OrderStatus
    items: list[OrderItemResponse] = []
    total_kg: Optional[float] = None
    total: Optional[StockWeightResponse] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

    @model_validator(mode="after")
    def compute_total_units(self) -> "OrderResponse":
        total_kg = sum(float(i.cantidad_kg) for i in self.items)
        self.total_kg = total_kg
        self.total = StockWeightResponse(**weight_summary(total_kg))
        return self
