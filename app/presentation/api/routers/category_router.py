from typing import Optional
from math import ceil
from fastapi import APIRouter, Query, Depends

from app.application.dto.category_dto import CreateCategoryRequest, UpdateCategoryRequest, CategoryResponse
from app.application.use_cases.categories.category_use_cases import (
    CreateCategoryUseCase,
    GetCategoryUseCase,
    ListCategoriesUseCase,
    UpdateCategoryUseCase,
    DeleteCategoryUseCase,
)
from app.infrastructure.database.repositories.category_repository_impl import CategoryRepositoryImpl
from app.presentation.api.dependencies.auth_dependencies import AdminUser
from app.presentation.api.dependencies.db_dependencies import DbSession
from app.shared.responses.api_response import ApiResponse, PaginatedResponse
from app.presentation.api.dependencies.auth_dependencies import require_roles, CurrentUser
from app.shared.constants.roles import UserRole

router = APIRouter(prefix="/categorias", tags=["Categorías (Admin)"])


@router.post(
    "",
    response_model=ApiResponse[CategoryResponse],
    status_code=201,
    summary="Crear categoría",
    description="Crea una nueva categoría de productos de pescado.",
)
def create_category(request: CreateCategoryRequest, current_user: AdminUser, db: DbSession):
    repo = CategoryRepositoryImpl(db)
    result = CreateCategoryUseCase(repo).execute(request, created_by=current_user.id)
    return ApiResponse.created(data=result, message="Categoría creada exitosamente.")


@router.get(
    "",
    response_model=PaginatedResponse[CategoryResponse],
    summary="Listar categorías",
    dependencies=[Depends(require_roles([UserRole.ADMIN, UserRole.REPARTIDOR, UserRole.EMPLEADO]))],
)
def list_categories(
    current_user: CurrentUser,
    db: DbSession,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, description="Buscar por nombre o descripción"),
    activa: Optional[bool] = Query(None, description="Filtrar por estado activo"),
):
    repo = CategoryRepositoryImpl(db)
    categories, total = ListCategoriesUseCase(repo).execute(
        page=page, page_size=page_size, search=search, activa=activa
    )
    return PaginatedResponse(
        data=categories, total=total, page=page, page_size=page_size,
        total_pages=ceil(total / page_size) if total else 0,
    )


@router.get(
    "/{category_id}",
    response_model=ApiResponse[CategoryResponse],
    summary="Obtener categoría por ID",
)
def get_category(category_id: int, current_user: AdminUser, db: DbSession):
    repo = CategoryRepositoryImpl(db)
    result = GetCategoryUseCase(repo).execute(category_id)
    return ApiResponse.ok(data=result)


@router.put(
    "/{category_id}",
    response_model=ApiResponse[CategoryResponse],
    summary="Editar categoría",
)
def update_category(
    category_id: int, request: UpdateCategoryRequest, current_user: AdminUser, db: DbSession
):
    repo = CategoryRepositoryImpl(db)
    result = UpdateCategoryUseCase(repo).execute(category_id, request, updated_by=current_user.id)
    return ApiResponse.ok(data=result, message="Categoría actualizada exitosamente.")


@router.delete(
    "/{category_id}",
    response_model=ApiResponse,
    summary="Eliminar categoría (soft delete)",
)
def delete_category(category_id: int, current_user: AdminUser, db: DbSession):
    repo = CategoryRepositoryImpl(db)
    DeleteCategoryUseCase(repo).execute(category_id, deleted_by=current_user.id)
    return ApiResponse.ok(message="Categoría eliminada exitosamente.")
