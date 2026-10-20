from app.domain.entities.user import User
from app.domain.repositories.user_repository import UserRepository
from app.application.dto.user_dto import CreateUserRequest, UpdateUserRequest, UserResponse
from app.infrastructure.security.password_handler import hash_password
from app.shared.exceptions.custom_exceptions import (
    ConflictException,
    NotFoundException,
    ForbiddenException,
)
from app.shared.constants.roles import UserRole


class CreateUserUseCase:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def execute(self, request: CreateUserRequest, created_by: int) -> UserResponse:
        if self.user_repo.exists_by_username(request.username):
            raise ConflictException(f"El nombre de usuario '{request.username}' ya está en uso.")
        if self.user_repo.exists_by_correo(request.correo):
            raise ConflictException(f"El correo '{request.correo}' ya está registrado.")
        if self.user_repo.exists_by_documento(request.documento):
            raise ConflictException(f"El documento '{request.documento}' ya está registrado.")

        user = User(
            id=0,
            username=request.username,
            password_hash=hash_password(request.password),
            role=request.role,
            nombre=request.nombre,
            correo=request.correo,
            telefono=request.telefono,
            documento=request.documento,
            is_active=True,
            created_by=created_by,
            updated_by=created_by,
        )
        created = self.user_repo.create(user)
        return UserResponse(
            id=created.id,
            username=created.username,
            role=created.role,
            nombre=created.nombre,
            correo=created.correo,
            telefono=created.telefono,
            documento=created.documento,
            is_active=created.is_active,
            created_at=created.created_at,
            updated_at=created.updated_at,
        )


class GetUserUseCase:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def execute(self, user_id: int) -> UserResponse:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundException("Usuario", user_id)
        return UserResponse(
            id=user.id,
            username=user.username,
            role=user.role,
            nombre=user.nombre,
            correo=user.correo,
            telefono=user.telefono,
            documento=user.documento,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )


class ListUsersUseCase:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def execute(
        self,
        page: int = 1,
        page_size: int = 20,
        role: UserRole | None = None,
        search: str | None = None,
        is_active: bool | None = None,
    ) -> tuple[list[UserResponse], int]:
        users, total = self.user_repo.list(
            page=page, page_size=page_size, role=role, search=search, is_active=is_active
        )
        responses = [
            UserResponse(
                id=u.id,
                username=u.username,
                role=u.role,
                nombre=u.nombre,
                correo=u.correo,
                telefono=u.telefono,
                documento=u.documento,
                is_active=u.is_active,
                created_at=u.created_at,
                updated_at=u.updated_at,
            )
            for u in users
        ]
        return responses, total


class UpdateUserUseCase:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def execute(self, user_id: int, request: UpdateUserRequest, updated_by: int) -> UserResponse:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundException("Usuario", user_id)

        if request.username and request.username != user.username:
            if self.user_repo.exists_by_username(request.username, exclude_id=user_id):
                raise ConflictException(f"El username '{request.username}' ya está en uso.")
            user.username = request.username

        if request.correo and request.correo != user.correo:
            if self.user_repo.exists_by_correo(request.correo, exclude_id=user_id):
                raise ConflictException(f"El correo '{request.correo}' ya está registrado.")
            user.correo = request.correo

        if request.documento and request.documento != user.documento:
            if self.user_repo.exists_by_documento(request.documento, exclude_id=user_id):
                raise ConflictException(f"El documento '{request.documento}' ya está registrado.")
            user.documento = request.documento

        if request.password:
            user.password_hash = hash_password(request.password)
        if request.role is not None:
            user.role = request.role
        if request.nombre is not None:
            user.nombre = request.nombre
        if request.telefono is not None:
            user.telefono = request.telefono
        if request.is_active is not None:
            user.is_active = request.is_active

        user.updated_by = updated_by
        updated = self.user_repo.update(user)
        return UserResponse(
            id=updated.id,
            username=updated.username,
            role=updated.role,
            nombre=updated.nombre,
            correo=updated.correo,
            telefono=updated.telefono,
            documento=updated.documento,
            is_active=updated.is_active,
            created_at=updated.created_at,
            updated_at=updated.updated_at,
        )


class DeleteUserUseCase:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def execute(self, user_id: int, deleted_by: int) -> None:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundException("Usuario", user_id)
        if user_id == deleted_by:
            raise ForbiddenException("No puedes eliminar tu propio usuario.")
        self.user_repo.soft_delete(user_id, deleted_by)


class ReactivateUserUseCase:
    """Reactiva un usuario que fue eliminado (soft delete), restaurando is_active=True."""
    def __init__(self, user_repo):
        self.user_repo = user_repo

    def execute(self, user_id: int, updated_by: int):
        from app.shared.exceptions.custom_exceptions import NotFoundException
        user = self.user_repo.get_by_id_including_deleted(user_id)
        if not user:
            raise NotFoundException("Usuario", user_id)
        user.is_active = True
        user.deleted_at = None
        user.updated_by = updated_by
        updated = self.user_repo.reactivate(user_id, updated_by)
        from app.shared.utils.weight_converter import weight_summary
        return UserResponse(
            id=updated.id, username=updated.username, nombre=updated.nombre,
            correo=updated.correo, role=updated.role, telefono=updated.telefono,
            documento=updated.documento, is_active=updated.is_active,
            created_at=updated.created_at, updated_at=updated.updated_at,
        )


class HardDeleteUserUseCase:
    """Elimina un usuario de forma PERMANENTE (no reversible). Solo para usuarios inactivos."""
    def __init__(self, user_repo):
        self.user_repo = user_repo

    def execute(self, user_id: int, deleted_by: int):
        from app.shared.exceptions.custom_exceptions import NotFoundException, BusinessRuleException
        if user_id == deleted_by:
            raise BusinessRuleException("No puedes eliminarte a ti mismo definitivamente.")
        user = self.user_repo.get_by_id_including_deleted(user_id)
        if not user:
            raise NotFoundException("Usuario", user_id)
        if user.is_active:
            raise BusinessRuleException(
                "Solo se pueden eliminar definitivamente usuarios inactivos. Desactívalo primero."
            )
        self.user_repo.hard_delete(user_id)
