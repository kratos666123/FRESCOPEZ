from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, func
from app.domain.entities.delivery import Delivery, DeliveryItem
from app.domain.repositories.delivery_repository import DeliveryRepository
from app.infrastructure.database.models.delivery_model import DeliveryModel, DeliveryItemModel
from app.shared.constants.roles import DeliveryType, DeliveryStatus


def _item_to_entity(m: DeliveryItemModel) -> DeliveryItem:
    from decimal import Decimal as _D
    return DeliveryItem(
        id=m.id,
        entrega_id=m.entrega_id,
        producto_id=m.producto_id,
        cantidad_kg=m.cantidad_kg,
        precio_compra_unitario_kg=m.precio_compra_unitario_kg if m.precio_compra_unitario_kg is not None else _D("0"),
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


def _model_to_entity(m: DeliveryModel) -> Delivery:
    return Delivery(
        id=m.id,
        tipo=DeliveryType(m.tipo),
        estado=DeliveryStatus(m.estado) if m.estado else DeliveryStatus.PENDIENTE,
        fecha_hora=m.fecha_hora,
        id_domiciliario=m.id_domiciliario,
        nombre_domiciliario=m.nombre_domiciliario,
        id_vehiculo=m.id_vehiculo,
        observaciones=m.observaciones,
        items=[_item_to_entity(i) for i in (m.items or [])],
        created_at=m.created_at,
        updated_at=m.updated_at,
        deleted_at=m.deleted_at,
        created_by=m.created_by,
        updated_by=m.updated_by,
    )


class DeliveryRepositoryImpl(DeliveryRepository):

    def __init__(self, db: Session):
        self.db = db

    def create(self, delivery: Delivery) -> Delivery:
        model = DeliveryModel(
            tipo=delivery.tipo,
            estado=delivery.estado.value if hasattr(delivery.estado, 'value') else delivery.estado,
            fecha_hora=delivery.fecha_hora,
            id_domiciliario=delivery.id_domiciliario,
            nombre_domiciliario=delivery.nombre_domiciliario,
            id_vehiculo=delivery.id_vehiculo,
            observaciones=delivery.observaciones,
            created_by=delivery.created_by,
            updated_by=delivery.updated_by,
        )
        for item in delivery.items:
            model.items.append(
                DeliveryItemModel(
                    producto_id=item.producto_id,
                    cantidad_kg=item.cantidad_kg,
                    precio_compra_unitario_kg=item.precio_compra_unitario_kg,
                )
            )
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        stmt = select(DeliveryModel).options(selectinload(DeliveryModel.items)).where(DeliveryModel.id == model.id)
        model = self.db.execute(stmt).scalar_one()
        return _model_to_entity(model)

    def get_by_id(self, delivery_id: int) -> Optional[Delivery]:
        stmt = (
            select(DeliveryModel)
            .options(selectinload(DeliveryModel.items))
            .where(DeliveryModel.id == delivery_id, DeliveryModel.deleted_at.is_(None))
        )
        model = self.db.execute(stmt).scalar_one_or_none()
        return _model_to_entity(model) if model else None

    def list(
        self,
        page: int = 1,
        page_size: int = 20,
        tipo: Optional[DeliveryType] = None,
        estado: Optional[DeliveryStatus] = None,
        id_domiciliario: Optional[int] = None,
        created_by: Optional[int] = None,
        search: Optional[str] = None,
    ) -> tuple[list[Delivery], int]:
        base_stmt = select(DeliveryModel).where(DeliveryModel.deleted_at.is_(None))
        if tipo is not None:
            base_stmt = base_stmt.where(DeliveryModel.tipo == tipo)
        if estado is not None:
            base_stmt = base_stmt.where(DeliveryModel.estado == estado)
        if id_domiciliario is not None:
            base_stmt = base_stmt.where(DeliveryModel.id_domiciliario == id_domiciliario)
        if created_by is not None:
            base_stmt = base_stmt.where(DeliveryModel.created_by == created_by)
        if search:
            pattern = f"%{search}%"
            base_stmt = base_stmt.where(DeliveryModel.observaciones.ilike(pattern))

        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        total = self.db.execute(count_stmt).scalar_one()

        stmt = (
            base_stmt
            .options(selectinload(DeliveryModel.items))
            .order_by(DeliveryModel.fecha_hora.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        models = self.db.execute(stmt).scalars().all()
        return [_model_to_entity(m) for m in models], total

    def update(self, delivery: Delivery) -> Delivery:
        stmt = (
            select(DeliveryModel)
            .options(selectinload(DeliveryModel.items))
            .where(DeliveryModel.id == delivery.id)
        )
        model = self.db.execute(stmt).scalar_one()
        model.tipo = delivery.tipo
        model.estado = delivery.estado.value if hasattr(delivery.estado, 'value') else delivery.estado
        model.fecha_hora = delivery.fecha_hora
        model.id_domiciliario = delivery.id_domiciliario
        model.nombre_domiciliario = delivery.nombre_domiciliario
        model.id_vehiculo = delivery.id_vehiculo
        model.observaciones = delivery.observaciones
        model.updated_by = delivery.updated_by
        model.items.clear()
        for item in delivery.items:
            model.items.append(
                DeliveryItemModel(
                    entrega_id=model.id,
                    producto_id=item.producto_id,
                    cantidad_kg=item.cantidad_kg,
                    precio_compra_unitario_kg=item.precio_compra_unitario_kg,
                )
            )
        self.db.commit()
        self.db.refresh(model)
        stmt = select(DeliveryModel).options(selectinload(DeliveryModel.items)).where(DeliveryModel.id == model.id)
        model = self.db.execute(stmt).scalar_one()
        return _model_to_entity(model)

    def soft_delete(self, delivery_id: int, deleted_by: int) -> bool:
        stmt = select(DeliveryModel).where(DeliveryModel.id == delivery_id, DeliveryModel.deleted_at.is_(None))
        model = self.db.execute(stmt).scalar_one_or_none()
        if not model:
            return False
        model.deleted_at = datetime.now(timezone.utc)
        model.updated_by = deleted_by
        self.db.commit()
        return True
