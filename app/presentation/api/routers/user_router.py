from typing import Optional
from fastapi import APIRouter, Query, Depends
from math import ceil

from app.application.dto.user_dto import CreateUserRequest, UpdateUserRequest, UserResponse
from app.application.use_cases.users.user_use_cases import (
    CreateUserUseCase,
    GetUserUseCase,
    ListUsersUseCase,
    UpdateUserUseCase,
    DeleteUserUseCase,
    ReactivateUserUseCase,
    HardDeleteUserUseCase,
)
from app.infrastructure.database.repositories.user_repository_impl import UserRepositoryImpl
from app.presentation.api.dependencies.auth_dependencies import (
    AdminUser,
    CurrentUser,
    RepartidorOrAdmin,
    EmpleadoOrAdmin,
    require_roles,
)
from app.presentation.api.dependencies.db_dependencies import DbSession
from app.shared.responses.api_response import ApiResponse, PaginatedResponse
from app.shared.constants.roles import UserRole

router = APIRouter(prefix="/usuarios", tags=["Usuarios (Admin)"])

@router.post(
    "",
    response_model=ApiResponse[UserResponse],
    status_code=201,
    summary="Crear usuario",
    description="Solo el administrador puede crear nuevos usuarios.",
)
def create_user(request: CreateUserRequest, current_user: AdminUser, db: DbSession):
    repo = UserRepositoryImpl(db)
    result = CreateUserUseCase(repo).execute(request, created_by=current_user.id)
    return ApiResponse.created(data=result, message="Usuario creado exitosamente.")

@router.get("/me", summary="Obtener perfil del usuario actual")
def get_current_user_profile(current_user: CurrentUser):
    return {
        "success": True,
        "data": {
            "nombre": current_user.nombre,
            "username": current_user.username,
            "role": current_user.role
        }
    }

@router.get("", response_model=PaginatedResponse[UserResponse], summary="Listar usuarios")
def list_users(
    current_user: EmpleadoOrAdmin,
    db: DbSession,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    search: Optional[str] = Query(None, description="Buscar por nombre, username, correo..."),
    role: Optional[UserRole] = Query(None, description="Filtrar por rol"),
    is_active: Optional[bool] = Query(None, description="Filtrar por estado activo"),
):
    repo = UserRepositoryImpl(db)
    users, total = ListUsersUseCase(repo).execute(
        page=page, page_size=page_size, role=role, search=search, is_active=is_active
    )
    return PaginatedResponse(
        data=users, total=total, page=page, page_size=page_size,
        total_pages=ceil(total / page_size) if total else 0,
    )


@router.get(
    "/inactivos",
    response_model=PaginatedResponse[UserResponse],
    summary="Listar usuarios inactivos/eliminados (Admin)",
    dependencies=[Depends(require_roles(UserRole.ADMIN))],
)
def list_inactive_users(
    db: DbSession,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    search: Optional[str] = Query(None),
):
    repo = UserRepositoryImpl(db)
    users, total = ListUsersUseCase(repo).execute(
        page=page, page_size=page_size, role=None, search=search, is_active=False
    )
    from math import ceil
    return PaginatedResponse(
        data=users, total=total, page=page, page_size=page_size,
        total_pages=ceil(total / page_size) if total else 0,
    )


@router.get(
    "/{user_id}",
    response_model=ApiResponse[UserResponse],
    summary="Obtener usuario por ID",
)
def get_user(user_id: int, current_user: AdminUser, db: DbSession):
    repo = UserRepositoryImpl(db)
    result = GetUserUseCase(repo).execute(user_id)
    return ApiResponse.ok(data=result)

@router.put(
    "/{user_id}",
    response_model=ApiResponse[UserResponse],
    summary="Editar usuario",
    description="Actualiza los datos del usuario. Todos los campos son opcionales.",
)
def update_user(user_id: int, request: UpdateUserRequest, current_user: AdminUser, db: DbSession):
    repo = UserRepositoryImpl(db)
    result = UpdateUserUseCase(repo).execute(user_id, request, updated_by=current_user.id)
    return ApiResponse.ok(data=result, message="Usuario actualizado exitosamente.")

@router.delete(
    "/{user_id}",
    response_model=ApiResponse,
    summary="Eliminar usuario (soft delete)",
    description="Elimina lógicamente al usuario. No se puede eliminar a uno mismo.",
)
def delete_user(user_id: int, current_user: AdminUser, db: DbSession):
    repo = UserRepositoryImpl(db)
    DeleteUserUseCase(repo).execute(user_id, deleted_by=current_user.id)
    return ApiResponse.ok(message="Usuario eliminado exitosamente.")

@router.post(
    "/{user_id}/reactivar",
    response_model=ApiResponse[UserResponse],
    summary="Reactivar usuario eliminado (Admin)",
)
def reactivate_user(user_id: int, current_user: AdminUser, db: DbSession):
    repo = UserRepositoryImpl(db)
    result = ReactivateUserUseCase(repo).execute(user_id, updated_by=current_user.id)
    return ApiResponse.ok(data=result, message="Usuario reactivado exitosamente.")


@router.delete(
    "/{user_id}/definitivo",
    response_model=ApiResponse,
    summary="Eliminar usuario permanentemente (Admin)",
    description="Eliminación PERMANENTE e irreversible. Solo para usuarios ya inactivos.",
)
def hard_delete_user(user_id: int, current_user: AdminUser, db: DbSession):
    repo = UserRepositoryImpl(db)
    HardDeleteUserUseCase(repo).execute(user_id, deleted_by=current_user.id)
    return ApiResponse.ok(message="Usuario eliminado permanentemente.")
