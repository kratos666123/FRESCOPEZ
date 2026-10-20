from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, model_validator
from app.shared.utils.weight_converter import weight_summary


class CreateProductRequest(BaseModel):
    categoria_id: int = Field(..., gt=0, examples=[1])
    nombre: str = Field(..., min_length=2, max_length=200, examples=["Tilapia"])
    descripcion: Optional[str] = Field(None, max_length=1000, examples=["Tilapia fresca, carne blanca"])
    precio: Decimal = Field(..., gt=0, decimal_places=4, examples=[["15000.0000"]], description="Precio de VENTA por kg")
    precio_compra_kg: Decimal = Field(Decimal("0"), ge=0, decimal_places=4, examples=[["10000.0000"]], description="Precio de COMPRA por kg")
    stock_kg: Decimal = Field(Decimal("0"), ge=0, decimal_places=6, examples=[["500.000000"]])
    imagen: Optional[str] = Field(None, max_length=500)
    activo: bool = Field(True)

    model_config = {"str_strip_whitespace": True}


class UpdateProductRequest(BaseModel):
    categoria_id: Optional[int] = Field(None, gt=0)
    nombre: Optional[str] = Field(None, min_length=2, max_length=200)
    descripcion: Optional[str] = Field(None, max_length=1000)
    precio: Optional[Decimal] = Field(None, gt=0, decimal_places=4, description="Precio de VENTA por kg")
    precio_compra_kg: Optional[Decimal] = Field(None, ge=0, decimal_places=4, description="Precio de COMPRA por kg")
    stock_kg: Optional[Decimal] = Field(None, ge=0, decimal_places=6)
    imagen: Optional[str] = Field(None, max_length=500)
    activo: Optional[bool] = None

    model_config = {"str_strip_whitespace": True}


class UpdateStockRequest(BaseModel):
    """Solo para empleados: actualizar únicamente el stock."""
    stock_kg: Decimal = Field(..., ge=0, decimal_places=6, examples=[["750.500000"]])


class StockWeightResponse(BaseModel):
    kg: float
    lb: float
    ton: float
    oz: float


class ProductResponse(BaseModel):
    id: int
    categoria_id: int
    nombre: str
    descripcion: Optional[str] = None
    precio: Decimal                        # precio VENTA por kg
    precio_compra_kg: Decimal = Decimal("0")  # precio COMPRA por kg
    margen_kg: Optional[Decimal] = None   # ganancia por kg (precio - precio_compra)
    stock_kg: Decimal
    stock: Optional[StockWeightResponse] = None
    imagen: Optional[str] = None
    activo: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

    @model_validator(mode="after")
    def compute_stock_units(self) -> "ProductResponse":
        summary = weight_summary(self.stock_kg)
        self.stock = StockWeightResponse(**summary)
        self.margen_kg = self.precio - self.precio_compra_kg
        return self


class ProductStockResponse(BaseModel):
    """Respuesta mínima para empleados (solo stock)."""
    id: int
    nombre: str
    stock_kg: Decimal
    stock: Optional[StockWeightResponse] = None
    activo: bool

    model_config = {"from_attributes": True}

    @model_validator(mode="after")
    def compute_stock_units(self) -> "ProductStockResponse":
        summary = weight_summary(self.stock_kg)
        self.stock = StockWeightResponse(**summary)
        return self
