from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select, func, or_
from app.domain.entities.order import Order, OrderItem
from app.domain.repositories.order_repository import OrderRepository
from app.infrastructure.database.models.order_model import OrderModel, OrderItemModel
from app.shared.constants.roles import OrderStatus


def _item_to_entity(m: OrderItemModel) -> OrderItem:
    return OrderItem(
        id=m.id,
        pedido_id=m.pedido_id,
        producto_id=m.producto_id,
        cantidad_kg=m.cantidad_kg,
        precio_unitario_kg=m.precio_unitario_kg,
        precio_compra_unitario_kg=m.precio_compra_unitario_kg if m.precio_compra_unitario_kg is not None else Decimal("0"),
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


def _model_to_entity(m: OrderModel) -> Order:
    return Order(
        id=m.id,
        nombre_cliente=m.nombre_cliente,
        documento_cliente=m.documento_cliente,
        id_domiciliario=m.id_domiciliario,
        nombre_domiciliario=m.nombre_domiciliario,
        id_vehiculo=m.id_vehiculo,
        lugar=m.lugar,
        fecha_hora=m.fecha_hora,
        precio_total=m.precio_total,
        estado=OrderStatus(m.estado),
        items=[_item_to_entity(i) for i in (m.items or [])],
        created_at=m.created_at,
        updated_at=m.updated_at,
        deleted_at=m.deleted_at,
        created_by=m.created_by,
        updated_by=m.updated_by,
    )


class OrderRepositoryImpl(OrderRepository):

    def __init__(self, db: Session):
        self.db = db

    def create(self, order: Order) -> Order:
        model = OrderModel(
            nombre_cliente=order.nombre_cliente,
            documento_cliente=order.documento_cliente,
            id_domiciliario=order.id_domiciliario,
            nombre_domiciliario=order.nombre_domiciliario,
            id_vehiculo=order.id_vehiculo,
            lugar=order.lugar,
            fecha_hora=order.fecha_hora,
            precio_total=order.precio_total,
            estado=order.estado,
            created_by=order.created_by,
            updated_by=order.updated_by,
        )
        for item in order.items:
            model.items.append(
                OrderItemModel(
                    producto_id=item.producto_id,
                    cantidad_kg=item.cantidad_kg,
                    precio_unitario_kg=item.precio_unitario_kg,
                    precio_compra_unitario_kg=item.precio_compra_unitario_kg,
                )
            )
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        stmt = select(OrderModel).options(selectinload(OrderModel.items)).where(OrderModel.id == model.id)
        model = self.db.execute(stmt).scalar_one()
        return _model_to_entity(model)

    def get_by_id(self, order_id: int) -> Optional[Order]:
        stmt = (
            select(OrderModel)
            .options(selectinload(OrderModel.items))
            .where(OrderModel.id == order_id, OrderModel.deleted_at.is_(None))
        )
        model = self.db.execute(stmt).scalar_one_or_none()
        return _model_to_entity(model) if model else None

    def list(
        self,
        page: int = 1,
        page_size: int = 20,
        id_domiciliario: Optional[int] = None,
        estado: Optional[OrderStatus] = None,
        search: Optional[str] = None,
    ) -> tuple[list[Order], int]:
        base_stmt = select(OrderModel).where(OrderModel.deleted_at.is_(None))
        if id_domiciliario is not None:
            base_stmt = base_stmt.where(OrderModel.id_domiciliario == id_domiciliario)
        if estado is not None:
            base_stmt = base_stmt.where(OrderModel.estado == estado)
        if search:
            pattern = f"%{search}%"
            base_stmt = base_stmt.where(
                or_(
                    OrderModel.nombre_cliente.ilike(pattern),
                    OrderModel.lugar.ilike(pattern),
                    OrderModel.documento_cliente.ilike(pattern),
                )
            )
        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        total = self.db.execute(count_stmt).scalar_one()
        stmt = (
            base_stmt
            .options(selectinload(OrderModel.items))
            .order_by(OrderModel.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        models = self.db.execute(stmt).scalars().all()
        return [_model_to_entity(m) for m in models], total

    def update(self, order: Order) -> Order:
        stmt = (
            select(OrderModel)
            .options(selectinload(OrderModel.items))
            .where(OrderModel.id == order.id)
        )
        model = self.db.execute(stmt).scalar_one()
        model.nombre_cliente = order.nombre_cliente
        model.documento_cliente = order.documento_cliente
        model.id_domiciliario = order.id_domiciliario
        model.nombre_domiciliario = order.nombre_domiciliario
        model.id_vehiculo = order.id_vehiculo
        model.lugar = order.lugar
        model.fecha_hora = order.fecha_hora
        model.precio_total = order.precio_total
        model.estado = order.estado
        model.updated_by = order.updated_by
        model.items.clear()
        for item in order.items:
            model.items.append(
                OrderItemModel(
                    pedido_id=model.id,
                    producto_id=item.producto_id,
                    cantidad_kg=item.cantidad_kg,
                    precio_unitario_kg=item.precio_unitario_kg,
                    precio_compra_unitario_kg=item.precio_compra_unitario_kg,
                )
            )
        self.db.commit()
        self.db.refresh(model)
        stmt = select(OrderModel).options(selectinload(OrderModel.items)).where(OrderModel.id == model.id)
        model = self.db.execute(stmt).scalar_one()
        return _model_to_entity(model)

    def soft_delete(self, order_id: int, deleted_by: int) -> bool:
        stmt = select(OrderModel).where(OrderModel.id == order_id, OrderModel.deleted_at.is_(None))
        model = self.db.execute(stmt).scalar_one_or_none()
        if not model:
            return False
        model.deleted_at = datetime.now(timezone.utc)
        model.updated_by = deleted_by
        self.db.commit()
        return True
