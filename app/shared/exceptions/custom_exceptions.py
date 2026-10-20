from typing import Any


class AppException(Exception):
    """Base application exception."""

    def __init__(self, message: str, status_code: int = 400, errors: list[Any] | None = None):
        self.message = message
        self.status_code = status_code
        self.errors = errors or []
        super().__init__(message)


class NotFoundException(AppException):
    """Resource not found."""

    def __init__(self, resource: str, identifier: Any = None):
        msg = f"{resource} no encontrado"
        if identifier is not None:
            msg = f"{resource} con id '{identifier}' no encontrado"
        super().__init__(message=msg, status_code=404)


class UnauthorizedException(AppException):
    """Authentication required."""

    def __init__(self, message: str = "No autorizado. Credenciales inválidas o sesión expirada."):
        super().__init__(message=message, status_code=401)


class ForbiddenException(AppException):
    """Access denied."""

    def __init__(self, message: str = "Acceso denegado. No tiene permisos para realizar esta acción."):
        super().__init__(message=message, status_code=403)


class ConflictException(AppException):
    """Resource already exists."""

    def __init__(self, message: str):
        super().__init__(message=message, status_code=409)


class ValidationException(AppException):
    """Business validation error."""

    def __init__(self, message: str, errors: list[Any] | None = None):
        super().__init__(message=message, status_code=422, errors=errors or [])


class BusinessRuleException(AppException):
    """Business logic rule violation."""

    def __init__(self, message: str):
        super().__init__(message=message, status_code=400)


class InsufficientStockException(BusinessRuleException):
    """Not enough stock for the requested quantity."""

    def __init__(self, product_name: str, available: float, requested: float):
        super().__init__(
            message=(
                f"Stock insuficiente para '{product_name}'. "
                f"Disponible: {available:.3f} kg, Solicitado: {requested:.3f} kg."
            )
        )
