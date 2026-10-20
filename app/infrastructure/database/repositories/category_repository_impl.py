from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, func, or_
from app.domain.entities.category import Category
from app.domain.repositories.category_repository import CategoryRepository
from app.infrastructure.database.models.category_model import CategoryModel


def _model_to_entity(m: CategoryModel) -> Category:
    return Category(
        id=m.id,
        nombre=m.nombre,
        descripcion=m.descripcion,
        activa=m.activa,
        created_at=m.created_at,
        updated_at=m.updated_at,
        deleted_at=m.deleted_at,
        created_by=m.created_by,
        updated_by=m.updated_by,
    )


class CategoryRepositoryImpl(CategoryRepository):

    def __init__(self, db: Session):
        self.db = db

    def create(self, category: Category) -> Category:
        model = CategoryModel(
            nombre=category.nombre,
            descripcion=category.descripcion,
            activa=category.activa,
            created_by=category.created_by,
            updated_by=category.updated_by,
        )
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return _model_to_entity(model)

    def get_by_id(self, category_id: int) -> Optional[Category]:
        stmt = select(CategoryModel).where(CategoryModel.id == category_id, CategoryModel.deleted_at.is_(None))
        model = self.db.execute(stmt).scalar_one_or_none()
        return _model_to_entity(model) if model else None

    def list(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        activa: Optional[bool] = None,
    ) -> tuple[list[Category], int]:
        stmt = select(CategoryModel).where(CategoryModel.deleted_at.is_(None))
        if activa is not None:
            stmt = stmt.where(CategoryModel.activa == activa)
        if search:
            pattern = f"%{search}%"
            stmt = stmt.where(
                or_(CategoryModel.nombre.ilike(pattern), CategoryModel.descripcion.ilike(pattern))
            )
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.db.execute(count_stmt).scalar_one()
        stmt = stmt.order_by(CategoryModel.nombre.asc()).offset((page - 1) * page_size).limit(page_size)
        models = self.db.execute(stmt).scalars().all()
        return [_model_to_entity(m) for m in models], total

    def update(self, category: Category) -> Category:
        stmt = select(CategoryModel).where(CategoryModel.id == category.id)
        model = self.db.execute(stmt).scalar_one()
        model.nombre = category.nombre
        model.descripcion = category.descripcion
        model.activa = category.activa
        model.updated_by = category.updated_by
        self.db.commit()
        self.db.refresh(model)
        return _model_to_entity(model)

    def soft_delete(self, category_id: int, deleted_by: int) -> bool:
        stmt = select(CategoryModel).where(CategoryModel.id == category_id, CategoryModel.deleted_at.is_(None))
        model = self.db.execute(stmt).scalar_one_or_none()
        if not model:
            return False
        model.deleted_at = datetime.now(timezone.utc)
        model.activa = False
        model.updated_by = deleted_by
        self.db.commit()
        return True

    def exists_by_nombre(self, nombre: str, exclude_id: Optional[int] = None) -> bool:
        stmt = select(func.count()).where(CategoryModel.nombre == nombre, CategoryModel.deleted_at.is_(None))
        if exclude_id:
            stmt = stmt.where(CategoryModel.id != exclude_id)
        return self.db.execute(stmt).scalar_one() > 0
