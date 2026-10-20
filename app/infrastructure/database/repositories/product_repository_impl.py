from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, func, or_
from app.domain.entities.product import Product
from app.domain.repositories.product_repository import ProductRepository
from app.infrastructure.database.models.product_model import ProductModel


def _model_to_entity(m: ProductModel) -> Product:
    return Product(
        id=m.id,
        categoria_id=m.categoria_id,
        nombre=m.nombre,
        descripcion=m.descripcion,
        precio=m.precio,
        precio_compra_kg=m.precio_compra_kg if m.precio_compra_kg is not None else Decimal("0"),
        stock_kg=m.stock_kg,
        imagen=m.imagen,
        activo=m.activo,
        created_at=m.created_at,
        updated_at=m.updated_at,
        deleted_at=m.deleted_at,
        created_by=m.created_by,
        updated_by=m.updated_by,
    )


class ProductRepositoryImpl(ProductRepository):

    def __init__(self, db: Session):
        self.db = db

    def create(self, product: Product) -> Product:
        model = ProductModel(
            categoria_id=product.categoria_id,
            nombre=product.nombre,
            descripcion=product.descripcion,
            precio=product.precio,
            precio_compra_kg=product.precio_compra_kg,
            stock_kg=product.stock_kg,
            imagen=product.imagen,
            activo=product.activo,
            created_by=product.created_by,
            updated_by=product.updated_by,
        )
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return _model_to_entity(model)

    def get_by_id(self, product_id: int) -> Optional[Product]:
        stmt = select(ProductModel).where(ProductModel.id == product_id, ProductModel.deleted_at.is_(None))
        model = self.db.execute(stmt).scalar_one_or_none()
        return _model_to_entity(model) if model else None

    def list(
        self,
        page: int = 1,
        page_size: int = 20,
        categoria_id: Optional[int] = None,
        search: Optional[str] = None,
        activo: Optional[bool] = None,
    ) -> tuple[list[Product], int]:
        stmt = select(ProductModel).where(ProductModel.deleted_at.is_(None))
        if categoria_id is not None:
            stmt = stmt.where(ProductModel.categoria_id == categoria_id)
        if activo is not None:
            stmt = stmt.where(ProductModel.activo == activo)
        if search:
            pattern = f"%{search}%"
            stmt = stmt.where(
                or_(ProductModel.nombre.ilike(pattern), ProductModel.descripcion.ilike(pattern))
            )
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.db.execute(count_stmt).scalar_one()
        stmt = stmt.order_by(ProductModel.nombre.asc()).offset((page - 1) * page_size).limit(page_size)
        models = self.db.execute(stmt).scalars().all()
        return [_model_to_entity(m) for m in models], total

    def update(self, product: Product) -> Product:
        stmt = select(ProductModel).where(ProductModel.id == product.id)
        model = self.db.execute(stmt).scalar_one()
        model.categoria_id = product.categoria_id
        model.nombre = product.nombre
        model.descripcion = product.descripcion
        model.precio = product.precio
        model.precio_compra_kg = product.precio_compra_kg
        model.stock_kg = product.stock_kg
        model.activo = product.activo
        model.updated_by = product.updated_by
        if product.imagen is not None:
            model.imagen = product.imagen
        self.db.commit()
        self.db.refresh(model)
        return _model_to_entity(model)

    def update_stock(self, product_id: int, new_stock_kg: Decimal, updated_by: int) -> Product:
        stmt = select(ProductModel).where(ProductModel.id == product_id, ProductModel.deleted_at.is_(None))
        model = self.db.execute(stmt).scalar_one()
        model.stock_kg = new_stock_kg
        model.updated_by = updated_by
        self.db.commit()
        self.db.refresh(model)
        return _model_to_entity(model)

    def soft_delete(self, product_id: int, deleted_by: int) -> bool:
        stmt = select(ProductModel).where(ProductModel.id == product_id, ProductModel.deleted_at.is_(None))
        model = self.db.execute(stmt).scalar_one_or_none()
        if not model:
            return False
        model.deleted_at = datetime.now(timezone.utc)
        model.activo = False
        model.updated_by = deleted_by
        self.db.commit()
        return True

    def exists_by_nombre(self, nombre: str, exclude_id: Optional[int] = None) -> bool:
        stmt = select(func.count()).where(ProductModel.nombre == nombre, ProductModel.deleted_at.is_(None))
        if exclude_id:
            stmt = stmt.where(ProductModel.id != exclude_id)
        return self.db.execute(stmt).scalar_one() > 0
