import enum
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, Enum, Integer, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.infrastructure.database.session import Base
from app.shared.constants.roles import UserRole


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
    Enum(
        UserRole,
        values_callable=lambda enum: [e.value for e in enum],
        name="user_role_enum",
    ),
    nullable=False,
    default=UserRole.EMPLEADO,
    index=True,
)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    correo: Mapped[str] = mapped_column(String(150), unique=True, nullable=False, index=True)
    telefono: Mapped[str | None] = mapped_column(String(30), nullable=True)
    documento: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Audit fields
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    created_by: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_by: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    refresh_tokens: Mapped[list["RefreshTokenModel"]] = relationship(
        "RefreshTokenModel", back_populates="user", cascade="all, delete-orphan"
    )
    orders_as_driver: Mapped[list["OrderModel"]] = relationship(
        "OrderModel", back_populates="domiciliario", foreign_keys="OrderModel.id_domiciliario"
    )

    def __repr__(self) -> str:
        return f"<UserModel id={self.id} username={self.username} role={self.role}>"


# Avoid circular import by importing at the bottom
from app.infrastructure.database.models.token_model import RefreshTokenModel  # noqa: E402
from app.infrastructure.database.models.order_model import OrderModel  # noqa: E402
