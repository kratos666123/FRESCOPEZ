"""Add vehicles table, delivery estado/domiciliario/vehiculo, order id_vehiculo

Revision ID: 002_vehicles_and_delivery_updates
Revises: 001_initial
Create Date: 2026-09-05 00:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "002_vehicles_and_delivery_updates"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── vehicles ──────────────────────────────────────────────────────────────
    op.create_table(
        "vehicles",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("placa", sa.String(20), nullable=False),
        sa.Column("color", sa.String(50), nullable=False),
        sa.Column("tipo_vehiculo", sa.String(100), nullable=False),
        sa.Column("capacidad_kg", sa.Numeric(14, 4), nullable=False),
        sa.Column("carga_actual_kg", sa.Numeric(14, 4), nullable=False, server_default="0"),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("NOW() ON UPDATE NOW()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("placa"),
    )
    op.create_index("ix_vehicles_placa", "vehicles", ["placa"])
    op.create_index("ix_vehicles_deleted_at", "vehicles", ["deleted_at"])

    # ── deliveries: add estado, id_domiciliario, id_vehiculo ──────────────────
    # Add estado enum column
    op.add_column(
        "deliveries",
        sa.Column(
            "estado",
            sa.Enum("pendiente", "en_proceso", "completada", "cancelada", name="delivery_status_enum"),
            nullable=False,
            server_default="pendiente",
        ),
    )
    op.add_column(
        "deliveries",
        sa.Column("id_domiciliario", sa.Integer(), nullable=True),
    )
    op.add_column(
        "deliveries",
        sa.Column("id_vehiculo", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_deliveries_id_domiciliario",
        "deliveries", "users",
        ["id_domiciliario"], ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_deliveries_id_vehiculo",
        "deliveries", "vehicles",
        ["id_vehiculo"], ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_deliveries_estado", "deliveries", ["estado"])

    # ── orders: add id_vehiculo ───────────────────────────────────────────────
    op.add_column(
        "orders",
        sa.Column("id_vehiculo", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_orders_id_vehiculo",
        "orders", "vehicles",
        ["id_vehiculo"], ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    # orders
    op.drop_constraint("fk_orders_id_vehiculo", "orders", type_="foreignkey")
    op.drop_column("orders", "id_vehiculo")

    # deliveries
    op.drop_index("ix_deliveries_estado", "deliveries")
    op.drop_constraint("fk_deliveries_id_vehiculo", "deliveries", type_="foreignkey")
    op.drop_constraint("fk_deliveries_id_domiciliario", "deliveries", type_="foreignkey")
    op.drop_column("deliveries", "id_vehiculo")
    op.drop_column("deliveries", "id_domiciliario")
    op.drop_column("deliveries", "estado")
    op.execute("DROP TYPE IF EXISTS delivery_status_enum")

    # vehicles
    op.drop_index("ix_vehicles_deleted_at", "vehicles")
    op.drop_index("ix_vehicles_placa", "vehicles")
    op.drop_table("vehicles")
