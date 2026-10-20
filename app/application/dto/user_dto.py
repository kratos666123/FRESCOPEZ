from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, EmailStr
from app.shared.constants.roles import UserRole


class CreateUserRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=100, examples=["juan_repartidor"])
    password: str = Field(..., min_length=8, max_length=128, examples=["MiPassword123!"])
    role: UserRole = Field(..., examples=[UserRole.REPARTIDOR])
    nombre: str = Field(..., min_length=2, max_length=150, examples=["Juan Pérez"])
    correo: EmailStr = Field(..., examples=["juan@empresa.com"])
    telefono: Optional[str] = Field(None, max_length=30, examples=["3001234567"])
    documento: str = Field(..., min_length=5, max_length=50, examples=["1023456789"])

    model_config = {"str_strip_whitespace": True}


class UpdateUserRequest(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    password: Optional[str] = Field(None, min_length=8, max_length=128)
    role: Optional[UserRole] = None
    nombre: Optional[str] = Field(None, min_length=2, max_length=150)
    correo: Optional[EmailStr] = None
    telefono: Optional[str] = Field(None, max_length=30)
    documento: Optional[str] = Field(None, min_length=5, max_length=50)
    is_active: Optional[bool] = None

    model_config = {"str_strip_whitespace": True}


class UserResponse(BaseModel):
    id: int
    username: str
    role: UserRole
    nombre: str
    correo: str
    telefono: Optional[str] = None
    documento: str
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    id: int
    username: str
    role: UserRole
    nombre: str
    correo: str
    is_active: bool

    model_config = {"from_attributes": True}
