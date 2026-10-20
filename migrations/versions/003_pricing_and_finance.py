"""Add precio_compra_kg to products and precio_compra_unitario_kg to delivery_items

Revision ID: 003_pricing_and_finance
Revises: 002_vehicles_and_delivery_updates
Create Date: 2026-09-06 00:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "003_pricing_and_finance"
down_revision: Union[str, None] = "002_vehicles_and_delivery_updates"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # products: precio_compra_kg (default 0, existing rows inherit 0)
    op.add_column(
        "products",
        sa.Column("precio_compra_kg", sa.Numeric(12, 4), nullable=False, server_default="0"),
    )

    # delivery_items: precio_compra_unitario_kg
    op.add_column(
        "delivery_items",
        sa.Column("precio_compra_unitario_kg", sa.Numeric(12, 4), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("delivery_items", "precio_compra_unitario_kg")
    op.drop_column("products", "precio_compra_kg")
