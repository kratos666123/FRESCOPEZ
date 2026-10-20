from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, model_validator
from app.shared.constants.roles import DeliveryType, DeliveryStatus
from app.shared.utils.weight_converter import weight_summary
from app.application.dto.product_dto import StockWeightResponse


class DeliveryItemRequest(BaseModel):
    id_producto: int = Field(..., gt=0, examples=[1])
    cantidad_kg: Decimal = Field(..., gt=0, decimal_places=6, examples=[["100.000000"]])

    model_config = {"str_strip_whitespace": True}


class CreateDeliveryRequest(BaseModel):
    # tipo siempre es COMPRA; no se expone en la request para evitar confusión
    fecha_hora: datetime = Field(..., examples=["2025-06-15T08:30:00"])
    id_domiciliario: int = Field(..., gt=0, description="Repartidor o admin asignado")
    id_vehiculo: int = Field(..., gt=0, description="Vehículo asignado (obligatorio)")
    items: list[DeliveryItemRequest] = Field(..., min_length=1)
    observaciones: Optional[str] = Field(None, max_length=1000)

    model_config = {"str_strip_whitespace": True}


class UpdateDeliveryRequest(BaseModel):
    # tipo no se puede cambiar: las entregas son siempre compra
    fecha_hora: Optional[datetime] = None
    estado: Optional[DeliveryStatus] = None
    id_domiciliario: Optional[int] = Field(None, gt=0)
    id_vehiculo: Optional[int] = Field(None, gt=0)
    items: Optional[list[DeliveryItemRequest]] = Field(None, min_length=1)
    observaciones: Optional[str] = Field(None, max_length=1000)

    model_config = {"str_strip_whitespace": True}


class DeliveryItemResponse(BaseModel):
    id: int
    producto_id: int
    cantidad_kg: Decimal
    precio_compra_unitario_kg: Decimal = Decimal("0")
    subtotal_compra: Optional[Decimal] = None
    cantidad: Optional[StockWeightResponse] = None

    model_config = {"from_attributes": True}

    @model_validator(mode="after")
    def compute_units(self) -> "DeliveryItemResponse":
        summary = weight_summary(self.cantidad_kg)
        self.cantidad = StockWeightResponse(**summary)
        self.subtotal_compra = self.cantidad_kg * self.precio_compra_unitario_kg
        return self


class DeliveryResponse(BaseModel):
    id: int
    tipo: DeliveryType
    estado: DeliveryStatus
    fecha_hora: datetime
    id_domiciliario: Optional[int] = None
    nombre_domiciliario: Optional[str] = None
    id_vehiculo: Optional[int] = None
    observaciones: Optional[str] = None
    items: list[DeliveryItemResponse] = []
    total_kg: Optional[float] = None
    total: Optional[StockWeightResponse] = None
    total_compra: Optional[Decimal] = None   # costo total de la entrega (compra)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

    @model_validator(mode="after")
    def compute_total_units(self) -> "DeliveryResponse":
        total_kg = sum(float(i.cantidad_kg) for i in self.items)
        self.total_kg = total_kg
        self.total = StockWeightResponse(**weight_summary(total_kg))
        self.total_compra = sum((i.subtotal_compra or Decimal("0")) for i in self.items)
        return self
