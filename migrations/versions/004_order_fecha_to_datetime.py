"""Order: fecha→fecha_hora, nombre_domiciliario snapshot, precio_compra_unitario_kg in order_items

Revision ID: 004_order_fecha_to_datetime
Revises: 003_pricing_and_finance
Create Date: 2026-09-09 00:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "004_order_fecha_to_datetime"
down_revision: Union[str, None] = "003_pricing_and_finance"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. orders.fecha (Date) → fecha_hora (DateTime)
    op.add_column("orders", sa.Column("fecha_hora", sa.DateTime(), nullable=True))
    op.execute("UPDATE orders SET fecha_hora = CAST(fecha AS DATETIME)")
    op.alter_column("orders", "fecha_hora", nullable=False)
    op.drop_column("orders", "fecha")
    op.create_index("ix_orders_fecha_hora", "orders", ["fecha_hora"])

    # 2. orders.id_domiciliario: RESTRICT → SET NULL (so deleting user doesn't cascade)
    op.drop_constraint("orders_ibfk_domiciliario", "orders", type_="foreignkey")
    op.alter_column("orders", "id_domiciliario", nullable=True)
    op.create_foreign_key(
        "fk_orders_id_domiciliario", "orders", "users",
        ["id_domiciliario"], ["id"], ondelete="SET NULL"
    )

    # 3. Snapshot nombre del domiciliario en orders y deliveries
    op.add_column("orders",
        sa.Column("nombre_domiciliario", sa.String(200), nullable=True))
    op.execute(
        "UPDATE orders o LEFT JOIN users u ON o.id_domiciliario = u.id "
        "SET o.nombre_domiciliario = u.nombre WHERE u.id IS NOT NULL"
    )
    op.add_column("deliveries",
        sa.Column("nombre_domiciliario", sa.String(200), nullable=True))
    op.execute(
        "UPDATE deliveries d LEFT JOIN users u ON d.id_domiciliario = u.id "
        "SET d.nombre_domiciliario = u.nombre WHERE u.id IS NOT NULL"
    )

    # 4. Snapshot precio_compra_unitario_kg en order_items
    op.add_column("order_items",
        sa.Column("precio_compra_unitario_kg", sa.Numeric(12, 4),
                  nullable=False, server_default="0"))


def downgrade() -> None:
    op.drop_column("order_items", "precio_compra_unitario_kg")
    op.drop_column("deliveries", "nombre_domiciliario")
    op.drop_column("orders", "nombre_domiciliario")
    op.drop_index("ix_orders_fecha_hora", "orders")
    op.add_column("orders", sa.Column("fecha", sa.Date(), nullable=True))
    op.execute("UPDATE orders SET fecha = DATE(fecha_hora)")
    op.alter_column("orders", "fecha", nullable=False)
    op.drop_column("orders", "fecha_hora")
