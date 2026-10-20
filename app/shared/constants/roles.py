from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    REPARTIDOR = "repartidor"
    EMPLEADO = "empleado"


class OrderStatus(str, Enum):
    PENDIENTE = "pendiente"
    EN_PROCESO = "en_proceso"
    ENTREGADO = "entregado"
    CANCELADO = "cancelado"


class DeliveryStatus(str, Enum):
    PENDIENTE = "pendiente"
    EN_PROCESO = "en_proceso"
    COMPLETADA = "completada"
    CANCELADA = "cancelada"


class DeliveryType(str, Enum):
    COMPRA = "compra"    # Incoming purchase (empresa compra al proveedor)
    VENTA = "venta"      # Outgoing delivery (empresa entrega al cliente)


class WeightUnit(str, Enum):
    KILOGRAMOS = "kg"
    LIBRAS = "lb"
    TONELADAS = "ton"
    ONZAS = "oz"


# RBAC Permission map
ROLE_PERMISSIONS: dict[str, list[str]] = {
    UserRole.ADMIN: [
        "auth:login",
        "users:create", "users:read", "users:update", "users:delete", "users:list",
        "categories:create", "categories:read", "categories:update", "categories:delete", "categories:list",
        "products:create", "products:read", "products:update", "products:delete", "products:list",
        "orders:create", "orders:read", "orders:update", "orders:delete", "orders:list",
        "deliveries:create", "deliveries:read", "deliveries:update", "deliveries:delete", "deliveries:list",
        "vehicles:create", "vehicles:read", "vehicles:update", "vehicles:delete", "vehicles:list",
    ],
    UserRole.REPARTIDOR: [
        "auth:login",
        "orders:read", "orders:update",
        "deliveries:update", "deliveries:read",
    ],
    UserRole.EMPLEADO: [
        "auth:login",
        "orders:create", "orders:read", "orders:update", "orders:delete",
        "deliveries:create", "deliveries:read", "deliveries:update",
        "products:read", "products:update_stock",
    ],
}
