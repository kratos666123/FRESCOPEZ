from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, func, or_
from app.domain.entities.user import User
from app.domain.repositories.user_repository import UserRepository
from app.infrastructure.database.models.user_model import UserModel
from app.shared.constants.roles import UserRole


def _model_to_entity(m: UserModel) -> User:
    return User(
        id=m.id,
        username=m.username,
        password_hash=m.password_hash,
        role=UserRole(m.role),
        nombre=m.nombre,
        correo=m.correo,
        telefono=m.telefono,
        documento=m.documento,
        is_active=m.is_active,
        created_at=m.created_at,
        updated_at=m.updated_at,
        deleted_at=m.deleted_at,
        created_by=m.created_by,
        updated_by=m.updated_by,
    )


class UserRepositoryImpl(UserRepository):

    def __init__(self, db: Session):
        self.db = db

    def create(self, user: User) -> User:
        model = UserModel(
            username=user.username,
            password_hash=user.password_hash,
            role=user.role,
            nombre=user.nombre,
            correo=user.correo,
            telefono=user.telefono,
            documento=user.documento,
            is_active=user.is_active,
            created_by=user.created_by,
            updated_by=user.updated_by,
        )
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return _model_to_entity(model)

    def get_by_id(self, user_id: int) -> Optional[User]:
        stmt = select(UserModel).where(UserModel.id == user_id, UserModel.deleted_at.is_(None))
        model = self.db.execute(stmt).scalar_one_or_none()
        return _model_to_entity(model) if model else None

    def get_by_username(self, username: str) -> Optional[User]:
        stmt = select(UserModel).where(UserModel.username == username, UserModel.deleted_at.is_(None))
        model = self.db.execute(stmt).scalar_one_or_none()
        return _model_to_entity(model) if model else None

    def get_by_documento(self, documento: str) -> Optional[User]:
        stmt = select(UserModel).where(UserModel.documento == documento, UserModel.deleted_at.is_(None))
        model = self.db.execute(stmt).scalar_one_or_none()
        return _model_to_entity(model) if model else None

    def get_by_correo(self, correo: str) -> Optional[User]:
        stmt = select(UserModel).where(UserModel.correo == correo, UserModel.deleted_at.is_(None))
        model = self.db.execute(stmt).scalar_one_or_none()
        return _model_to_entity(model) if model else None

    def list(
        self,
        page: int = 1,
        page_size: int = 20,
        role: Optional[UserRole] = None,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> tuple[list[User], int]:
        # When is_active=False, we need soft-deleted users (deleted_at IS NOT NULL)
        # When is_active=True or None, exclude soft-deleted (deleted_at IS NULL)
        if is_active is False:
            stmt = select(UserModel).where(UserModel.deleted_at.is_not(None))
        else:
            stmt = select(UserModel).where(UserModel.deleted_at.is_(None))
        if role:
            stmt = stmt.where(UserModel.role == role)
        if is_active is True:
            stmt = stmt.where(UserModel.is_active == True)
        if search:
            pattern = f"%{search}%"
            stmt = stmt.where(
                or_(
                    UserModel.nombre.ilike(pattern),
                    UserModel.username.ilike(pattern),
                    UserModel.correo.ilike(pattern),
                    UserModel.documento.ilike(pattern),
                )
            )
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.db.execute(count_stmt).scalar_one()
        stmt = stmt.order_by(UserModel.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        models = self.db.execute(stmt).scalars().all()
        return [_model_to_entity(m) for m in models], total

    def update(self, user: User) -> User:
        stmt = select(UserModel).where(UserModel.id == user.id)
        model = self.db.execute(stmt).scalar_one()
        model.username = user.username
        model.password_hash = user.password_hash
        model.role = user.role
        model.nombre = user.nombre
        model.correo = user.correo
        model.telefono = user.telefono
        model.documento = user.documento
        model.is_active = user.is_active
        model.updated_by = user.updated_by
        self.db.commit()
        self.db.refresh(model)
        return _model_to_entity(model)

    def soft_delete(self, user_id: int, deleted_by: int) -> bool:
        stmt = select(UserModel).where(UserModel.id == user_id, UserModel.deleted_at.is_(None))
        model = self.db.execute(stmt).scalar_one_or_none()
        if not model:
            return False
        model.deleted_at = datetime.now(timezone.utc)
        model.is_active = False
        model.updated_by = deleted_by
        self.db.commit()
        return True

    def exists_by_username(self, username: str, exclude_id: Optional[int] = None) -> bool:
        stmt = select(func.count()).where(UserModel.username == username, UserModel.deleted_at.is_(None))
        if exclude_id:
            stmt = stmt.where(UserModel.id != exclude_id)
        return self.db.execute(stmt).scalar_one() > 0

    def exists_by_correo(self, correo: str, exclude_id: Optional[int] = None) -> bool:
        stmt = select(func.count()).where(UserModel.correo == correo, UserModel.deleted_at.is_(None))
        if exclude_id:
            stmt = stmt.where(UserModel.id != exclude_id)
        return self.db.execute(stmt).scalar_one() > 0

    def exists_by_documento(self, documento: str, exclude_id: Optional[int] = None) -> bool:
        stmt = select(func.count()).where(UserModel.documento == documento, UserModel.deleted_at.is_(None))
        if exclude_id:
            stmt = stmt.where(UserModel.id != exclude_id)
        return self.db.execute(stmt).scalar_one() > 0

    def get_by_id_including_deleted(self, user_id: int):
        from sqlalchemy import select
        stmt = select(UserModel).where(UserModel.id == user_id)
        model = self.db.execute(stmt).scalar_one_or_none()
        return _model_to_entity(model) if model else None

    def reactivate(self, user_id: int, updated_by: int):
        from datetime import timezone
        from sqlalchemy import select
        stmt = select(UserModel).where(UserModel.id == user_id)
        model = self.db.execute(stmt).scalar_one_or_none()
        if not model:
            return None
        model.is_active = True
        model.deleted_at = None
        model.updated_by = updated_by
        self.db.commit()
        self.db.refresh(model)
        return _model_to_entity(model)

    def hard_delete(self, user_id: int) -> None:
        from sqlalchemy import select
        stmt = select(UserModel).where(UserModel.id == user_id)
        model = self.db.execute(stmt).scalar_one_or_none()
        if model:
            self.db.delete(model)
            self.db.commit()
