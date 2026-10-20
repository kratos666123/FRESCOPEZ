from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class CreateCategoryRequest(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=150, examples=["Pescado Blanco"])
    descripcion: Optional[str] = Field(None, max_length=1000, examples=["Categoría para pescados de carne blanca"])
    activa: bool = Field(True)

    model_config = {"str_strip_whitespace": True}


class UpdateCategoryRequest(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=150)
    descripcion: Optional[str] = Field(None, max_length=1000)
    activa: Optional[bool] = None

    model_config = {"str_strip_whitespace": True}


class CategoryResponse(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str] = None
    activa: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
