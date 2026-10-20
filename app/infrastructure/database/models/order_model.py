from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, Boolean, DateTime, Integer, ForeignKey, Numeric, Enum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.infrastructure.database.session import Base
from app.shared.constants.roles import OrderStatus


class OrderItemModel(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pedido_id: Mapped[int] = mapped_column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    producto_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    cantidad_kg: Mapped[Decimal] = mapped_column(Numeric(14, 6), nullable=False)
    precio_unitario_kg: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)       # precio venta snapshot
    precio_compra_unitario_kg: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False, server_default="0")  # precio compra snapshot

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    order: Mapped["OrderModel"] = relationship("OrderModel", back_populates="items")
    product: Mapped["ProductModel"] = relationship("ProductModel", back_populates="order_items")

    @property
    def precio(self) -> Decimal:
        if self.cantidad_kg and self.product and self.product.precio:
            try:
                precio_str = str(self.product.precio).strip()
                precio_producto = Decimal(precio_str)
                return self.cantidad_kg * precio_producto
            except (ValueError, TypeError):
                return Decimal("0.0")
        return Decimal("0.0")

    def __repr__(self) -> str:
        return f"<OrderItemModel pedido={self.pedido_id} producto={self.producto_id} cantidad={self.cantidad_kg}kg>"


class OrderModel(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre_cliente: Mapped[str] = mapped_column(String(200), nullable=False)
    documento_cliente: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    id_domiciliario: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    nombre_domiciliario: Mapped[str | None] = mapped_column(String(200), nullable=True)  # snapshot nombre al momento
    id_vehiculo: Mapped[int | None] = mapped_column(Integer, ForeignKey("vehicles.id", ondelete="SET NULL"), nullable=True)
    lugar: Mapped[str] = mapped_column(String(300), nullable=False)
    fecha_hora: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    precio_total: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    estado: Mapped[str] = mapped_column(
        Enum(OrderStatus, name="order_status_enum", values_callable=lambda x: [e.value for e in x]),
        default=OrderStatus.PENDIENTE,
        nullable=False,
        index=True,
    )

    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    created_by: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_by: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    items: Mapped[list[OrderItemModel]] = relationship(
        "OrderItemModel", back_populates="order", cascade="all, delete-orphan"
    )
    domiciliario: Mapped["UserModel"] = relationship(
        "UserModel", back_populates="orders_as_driver", foreign_keys=[id_domiciliario]
    )

    def __repr__(self) -> str:
        return f"<OrderModel id={self.id} cliente={self.nombre_cliente} estado={self.estado}>"


from app.infrastructure.database.models.user_model import UserModel  # noqa: E402
from app.infrastructure.database.models.product_model import ProductModel  # noqa: E402
