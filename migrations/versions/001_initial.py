"""Initial migration - create all tables

Revision ID: 001_initial
Revises:
Create Date: 2025-06-09 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── users ────────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("username", sa.String(100), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column(
            "role",
            sa.Enum("admin", "repartidor", "empleado", name="user_role_enum"),
            nullable=False,
            server_default="empleado",
        ),
        sa.Column("nombre", sa.String(150), nullable=False),
        sa.Column("correo", sa.String(150), nullable=False),
        sa.Column("telefono", sa.String(30), nullable=True),
        sa.Column("documento", sa.String(50), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("NOW() ON UPDATE NOW()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_users_username", "users", ["username"], unique=True)
    op.create_index("ix_users_correo", "users", ["correo"], unique=True)
    op.create_index("ix_users_documento", "users", ["documento"], unique=True)
    op.create_index("ix_users_role", "users", ["role"])
    op.create_index("ix_users_deleted_at", "users", ["deleted_at"])

    # ── refresh_tokens ────────────────────────────────────────────────────────
    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token", sa.String(length=512), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("is_revoked", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("NOW()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("token"),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])

    # ── categories ────────────────────────────────────────────────────────────
    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("nombre", sa.String(150), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("activa", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("NOW() ON UPDATE NOW()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("nombre"),
    )
    op.create_index("ix_categories_activa", "categories", ["activa"])
    op.create_index("ix_categories_deleted_at", "categories", ["deleted_at"])

    # ── products ──────────────────────────────────────────────────────────────
    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("categoria_id", sa.Integer(), nullable=False),
        sa.Column("nombre", sa.String(200), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=True),
        sa.Column("precio", sa.Numeric(12, 4), nullable=False),
        sa.Column("stock_kg", sa.Numeric(14, 6), nullable=False, server_default="0"),
        sa.Column("imagen", sa.String(500), nullable=True),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("NOW() ON UPDATE NOW()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["categoria_id"], ["categories.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("nombre"),
    )
    op.create_index("ix_products_categoria_id", "products", ["categoria_id"])
    op.create_index("ix_products_activo", "products", ["activo"])
    op.create_index("ix_products_deleted_at", "products", ["deleted_at"])

    # ── orders ────────────────────────────────────────────────────────────────
    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("nombre_cliente", sa.String(200), nullable=False),
        sa.Column("documento_cliente", sa.String(50), nullable=False),
        sa.Column("id_domiciliario", sa.Integer(), nullable=False),
        sa.Column("lugar", sa.String(300), nullable=False),
        sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("precio_total", sa.Numeric(14, 4), nullable=False),
        sa.Column(
            "estado",
            sa.Enum("pendiente", "en_proceso", "entregado", "cancelado", name="order_status_enum"),
            nullable=False,
            server_default="pendiente",
        ),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("NOW() ON UPDATE NOW()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["id_domiciliario"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_orders_id_domiciliario", "orders", ["id_domiciliario"])
    op.create_index("ix_orders_estado", "orders", ["estado"])
    op.create_index("ix_orders_fecha", "orders", ["fecha"])
    op.create_index("ix_orders_deleted_at", "orders", ["deleted_at"])
    op.create_index("ix_orders_documento_cliente", "orders", ["documento_cliente"])

    # ── order_items ───────────────────────────────────────────────────────────
    op.create_table(
        "order_items",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("pedido_id", sa.Integer(), nullable=False),
        sa.Column("producto_id", sa.Integer(), nullable=False),
        sa.Column("cantidad_kg", sa.Numeric(14, 6), nullable=False),
        sa.Column("precio_unitario_kg", sa.Numeric(12, 4), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("NOW() ON UPDATE NOW()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["pedido_id"], ["orders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["producto_id"], ["products.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_order_items_pedido_id", "order_items", ["pedido_id"])
    op.create_index("ix_order_items_producto_id", "order_items", ["producto_id"])

    # ── deliveries ────────────────────────────────────────────────────────────
    op.create_table(
        "deliveries",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column(
            "tipo",
            sa.Enum("compra", "venta", name="delivery_type_enum"),
            nullable=False,
        ),
        sa.Column("fecha_hora", sa.DateTime(), nullable=False),
        sa.Column("observaciones", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("NOW() ON UPDATE NOW()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_deliveries_tipo", "deliveries", ["tipo"])
    op.create_index("ix_deliveries_fecha_hora", "deliveries", ["fecha_hora"])
    op.create_index("ix_deliveries_deleted_at", "deliveries", ["deleted_at"])

    # ── delivery_items ────────────────────────────────────────────────────────
    op.create_table(
        "delivery_items",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("entrega_id", sa.Integer(), nullable=False),
        sa.Column("producto_id", sa.Integer(), nullable=False),
        sa.Column("cantidad_kg", sa.Numeric(14, 6), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("NOW() ON UPDATE NOW()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["entrega_id"], ["deliveries.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["producto_id"], ["products.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_delivery_items_entrega_id", "delivery_items", ["entrega_id"])
    op.create_index("ix_delivery_items_producto_id", "delivery_items", ["producto_id"])


def downgrade() -> None:
    op.drop_table("delivery_items")
    op.drop_table("deliveries")
    op.drop_table("order_items")
    op.drop_table("orders")
    op.drop_table("products")
    op.drop_table("categories")
    op.drop_table("refresh_tokens")
    op.drop_table("users")

    # Drop ENUM types (MySQL handles this automatically, but explicit for portability)
    op.execute("DROP TYPE IF EXISTS delivery_type_enum")
    op.execute("DROP TYPE IF EXISTS order_status_enum")
    op.execute("DROP TYPE IF EXISTS user_role_enum")
