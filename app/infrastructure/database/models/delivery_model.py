from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, Boolean, DateTime, Integer, ForeignKey, Numeric, Enum, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.infrastructure.database.session import Base
from app.shared.constants.roles import DeliveryType, DeliveryStatus


class DeliveryItemModel(Base):
    __tablename__ = "delivery_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entrega_id: Mapped[int] = mapped_column(Integer, ForeignKey("deliveries.id", ondelete="CASCADE"), nullable=False, index=True)
    producto_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, index=True)
    cantidad_kg: Mapped[Decimal] = mapped_column(Numeric(14, 6), nullable=False)
    precio_compra_unitario_kg: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False, server_default="0")  # precio compra snapshot

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    delivery: Mapped["DeliveryModel"] = relationship("DeliveryModel", back_populates="items")
    product: Mapped["ProductModel"] = relationship("ProductModel", back_populates="delivery_items")

    def __repr__(self) -> str:
        return f"<DeliveryItemModel entrega={self.entrega_id} producto={self.producto_id} cantidad={self.cantidad_kg}kg>"


class DeliveryModel(Base):
    __tablename__ = "deliveries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tipo: Mapped[str] = mapped_column(
        Enum(DeliveryType, name="delivery_type_enum", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True,
    )
    estado: Mapped[str] = mapped_column(
        Enum(DeliveryStatus, name="delivery_status_enum", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=DeliveryStatus.PENDIENTE.value,
        index=True,
    )
    fecha_hora: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    observaciones: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Assignment
    id_domiciliario: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    nombre_domiciliario: Mapped[str | None] = mapped_column(String(200), nullable=True)  # snapshot nombre al momento
    id_vehiculo: Mapped[int | None] = mapped_column(Integer, ForeignKey("vehicles.id", ondelete="SET NULL"), nullable=True)

    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    created_by: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_by: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    items: Mapped[list[DeliveryItemModel]] = relationship(
        "DeliveryItemModel", back_populates="delivery", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<DeliveryModel id={self.id} tipo={self.tipo} estado={self.estado} fecha={self.fecha_hora}>"


from app.infrastructure.database.models.product_model import ProductModel  # noqa: E402
