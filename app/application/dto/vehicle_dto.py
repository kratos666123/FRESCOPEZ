from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, model_validator
from app.shared.utils.weight_converter import weight_summary
from app.application.dto.product_dto import StockWeightResponse


class CreateVehicleRequest(BaseModel):
    placa: str = Field(..., min_length=3, max_length=20, examples=["ABC123"])
    color: str = Field(..., min_length=2, max_length=50, examples=["Blanco"])
    tipo_vehiculo: str = Field(..., min_length=2, max_length=100, examples=["Camión refrigerado"])
    capacidad_kg: Decimal = Field(..., gt=0, decimal_places=4, examples=["5000.0000"])

    model_config = {"str_strip_whitespace": True}


class UpdateVehicleRequest(BaseModel):
    placa: Optional[str] = Field(None, min_length=3, max_length=20)
    color: Optional[str] = Field(None, min_length=2, max_length=50)
    tipo_vehiculo: Optional[str] = Field(None, min_length=2, max_length=100)
    capacidad_kg: Optional[Decimal] = Field(None, gt=0, decimal_places=4)
    activo: Optional[bool] = None

    model_config = {"str_strip_whitespace": True}


class VehicleResponse(BaseModel):
    id: int
    placa: str
    color: str
    tipo_vehiculo: str
    capacidad_kg: Decimal
    carga_actual_kg: Decimal
    activo: bool
    capacidad: Optional[StockWeightResponse] = None
    carga_actual: Optional[StockWeightResponse] = None
    disponible: Optional[StockWeightResponse] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

    @model_validator(mode="after")
    def compute_units(self) -> "VehicleResponse":
        self.capacidad = StockWeightResponse(**weight_summary(self.capacidad_kg))
        self.carga_actual = StockWeightResponse(**weight_summary(self.carga_actual_kg))
        disponible_kg = max(Decimal("0"), self.capacidad_kg - self.carga_actual_kg)
        self.disponible = StockWeightResponse(**weight_summary(disponible_kg))
        return self
