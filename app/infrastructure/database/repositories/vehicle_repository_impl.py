from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, func, or_
from app.domain.entities.vehicle import Vehicle
from app.domain.repositories.vehicle_repository import VehicleRepository
from app.infrastructure.database.models.vehicle_model import VehicleModel


def _model_to_entity(m: VehicleModel) -> Vehicle:
    return Vehicle(
        id=m.id,
        placa=m.placa,
        color=m.color,
        tipo_vehiculo=m.tipo_vehiculo,
        capacidad_kg=m.capacidad_kg,
        carga_actual_kg=m.carga_actual_kg if m.carga_actual_kg is not None else Decimal("0"),
        activo=m.activo,
        created_at=m.created_at,
        updated_at=m.updated_at,
        deleted_at=m.deleted_at,
        created_by=m.created_by,
        updated_by=m.updated_by,
    )


class VehicleRepositoryImpl(VehicleRepository):

    def __init__(self, db: Session):
        self.db = db

    def create(self, vehicle: Vehicle) -> Vehicle:
        model = VehicleModel(
            placa=vehicle.placa.upper(),
            color=vehicle.color,
            tipo_vehiculo=vehicle.tipo_vehiculo,
            capacidad_kg=vehicle.capacidad_kg,
            carga_actual_kg=vehicle.carga_actual_kg,
            activo=vehicle.activo,
            created_by=vehicle.created_by,
            updated_by=vehicle.updated_by,
        )
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return _model_to_entity(model)

    def get_by_id(self, vehicle_id: int) -> Optional[Vehicle]:
        stmt = select(VehicleModel).where(
            VehicleModel.id == vehicle_id,
            VehicleModel.deleted_at.is_(None),
        )
        model = self.db.execute(stmt).scalar_one_or_none()
        return _model_to_entity(model) if model else None

    def get_by_placa(self, placa: str) -> Optional[Vehicle]:
        stmt = select(VehicleModel).where(
            VehicleModel.placa == placa.upper(),
            VehicleModel.deleted_at.is_(None),
        )
        model = self.db.execute(stmt).scalar_one_or_none()
        return _model_to_entity(model) if model else None

    def list(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
    ) -> tuple[list[Vehicle], int]:
        stmt = select(VehicleModel).where(VehicleModel.deleted_at.is_(None))
        if search:
            pattern = f"%{search}%"
            stmt = stmt.where(
                or_(
                    VehicleModel.placa.ilike(pattern),
                    VehicleModel.tipo_vehiculo.ilike(pattern),
                    VehicleModel.color.ilike(pattern),
                )
            )
        count_stmt = select(func.count()).select_from(
            select(VehicleModel).where(VehicleModel.deleted_at.is_(None)).subquery()
        )
        total = self.db.execute(count_stmt).scalar_one()
        stmt = stmt.order_by(VehicleModel.id.desc()).offset((page - 1) * page_size).limit(page_size)
        models = self.db.execute(stmt).scalars().all()
        return [_model_to_entity(m) for m in models], total

    def update(self, vehicle: Vehicle) -> Vehicle:
        stmt = select(VehicleModel).where(VehicleModel.id == vehicle.id)
        model = self.db.execute(stmt).scalar_one()
        model.placa = vehicle.placa.upper()
        model.color = vehicle.color
        model.tipo_vehiculo = vehicle.tipo_vehiculo
        model.capacidad_kg = vehicle.capacidad_kg
        model.carga_actual_kg = vehicle.carga_actual_kg
        model.activo = vehicle.activo
        model.updated_by = vehicle.updated_by
        self.db.commit()
        self.db.refresh(model)
        return _model_to_entity(model)

    def update_carga(self, vehicle_id: int, nueva_carga_kg: Decimal, updated_by: int) -> bool:
        stmt = select(VehicleModel).where(VehicleModel.id == vehicle_id, VehicleModel.deleted_at.is_(None))
        model = self.db.execute(stmt).scalar_one_or_none()
        if not model:
            return False
        model.carga_actual_kg = max(Decimal("0"), nueva_carga_kg)
        model.updated_by = updated_by
        self.db.commit()
        return True

    def soft_delete(self, vehicle_id: int, deleted_by: int) -> bool:
        stmt = select(VehicleModel).where(VehicleModel.id == vehicle_id, VehicleModel.deleted_at.is_(None))
        model = self.db.execute(stmt).scalar_one_or_none()
        if not model:
            return False
        model.deleted_at = datetime.now(timezone.utc)
        model.updated_by = deleted_by
        self.db.commit()
        return True
