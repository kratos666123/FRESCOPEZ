from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, Boolean, DateTime, Integer, ForeignKey, Text, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.infrastructure.database.session import Base


class ProductModel(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    categoria_id: Mapped[int] = mapped_column(Integer, ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False, index=True)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False, unique=True, index=True)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    precio: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)             # precio VENTA por kg
    precio_compra_kg: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False, server_default="0")  # precio COMPRA por kg
    stock_kg: Mapped[Decimal] = mapped_column(Numeric(14, 6), nullable=False, default=Decimal("0"))  # en kg
    imagen: Mapped[str | None] = mapped_column(String(500), nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)

    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    created_by: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_by: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    category: Mapped["CategoryModel"] = relationship("CategoryModel", back_populates="products")
    order_items: Mapped[list["OrderItemModel"]] = relationship("OrderItemModel", back_populates="product")
    delivery_items: Mapped[list["DeliveryItemModel"]] = relationship("DeliveryItemModel", back_populates="product")

    def __repr__(self) -> str:
        return f"<ProductModel id={self.id} nombre={self.nombre} stock={self.stock_kg}kg>"


from app.infrastructure.database.models.category_model import CategoryModel  # noqa: E402
from app.infrastructure.database.models.order_model import OrderItemModel  # noqa: E402
from app.infrastructure.database.models.delivery_model import DeliveryItemModel  # noqa: E402
