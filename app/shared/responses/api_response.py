from typing import Any, Generic, TypeVar
from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    success: bool
    message: str
    data: T | None = None

    @classmethod
    def ok(cls, data: Any = None, message: str = "Operación exitosa") -> "ApiResponse":
        return cls(success=True, message=message, data=data)

    @classmethod
    def created(cls, data: Any = None, message: str = "Recurso creado exitosamente") -> "ApiResponse":
        return cls(success=True, message=message, data=data)


class ApiErrorResponse(BaseModel):
    success: bool = False
    message: str
    errors: list[Any] = []

    @classmethod
    def error(cls, message: str, errors: list[Any] | None = None) -> "ApiErrorResponse":
        return cls(success=False, message=message, errors=errors or [])


class PaginatedResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str = "Operación exitosa"
    data: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int
