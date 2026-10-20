from app.domain.entities.category import Category
from app.domain.repositories.category_repository import CategoryRepository
from app.application.dto.category_dto import (
    CreateCategoryRequest,
    UpdateCategoryRequest,
    CategoryResponse,
)
from app.shared.exceptions.custom_exceptions import ConflictException, NotFoundException


class CreateCategoryUseCase:
    def __init__(self, category_repo: CategoryRepository):
        self.category_repo = category_repo

    def execute(self, request: CreateCategoryRequest, created_by: int) -> CategoryResponse:
        if self.category_repo.exists_by_nombre(request.nombre):
            raise ConflictException(f"La categoría '{request.nombre}' ya existe.")

        category = Category(
            id=0,
            nombre=request.nombre,
            descripcion=request.descripcion,
            activa=request.activa,
            created_by=created_by,
            updated_by=created_by,
        )
        created = self.category_repo.create(category)
        return _to_response(created)


class GetCategoryUseCase:
    def __init__(self, category_repo: CategoryRepository):
        self.category_repo = category_repo

    def execute(self, category_id: int) -> CategoryResponse:
        category = self.category_repo.get_by_id(category_id)
        if not category:
            raise NotFoundException("Categoría", category_id)
        return _to_response(category)


class ListCategoriesUseCase:
    def __init__(self, category_repo: CategoryRepository):
        self.category_repo = category_repo

    def execute(
        self,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
        activa: bool | None = None,
    ) -> tuple[list[CategoryResponse], int]:
        categories, total = self.category_repo.list(
            page=page, page_size=page_size, search=search, activa=activa
        )
        return [_to_response(c) for c in categories], total


class UpdateCategoryUseCase:
    def __init__(self, category_repo: CategoryRepository):
        self.category_repo = category_repo

    def execute(
        self, category_id: int, request: UpdateCategoryRequest, updated_by: int
    ) -> CategoryResponse:
        category = self.category_repo.get_by_id(category_id)
        if not category:
            raise NotFoundException("Categoría", category_id)

        if request.nombre and request.nombre != category.nombre:
            if self.category_repo.exists_by_nombre(request.nombre, exclude_id=category_id):
                raise ConflictException(f"La categoría '{request.nombre}' ya existe.")
            category.nombre = request.nombre

        if request.descripcion is not None:
            category.descripcion = request.descripcion
        if request.activa is not None:
            category.activa = request.activa

        category.updated_by = updated_by
        updated = self.category_repo.update(category)
        return _to_response(updated)


class DeleteCategoryUseCase:
    def __init__(self, category_repo: CategoryRepository):
        self.category_repo = category_repo

    def execute(self, category_id: int, deleted_by: int) -> None:
        category = self.category_repo.get_by_id(category_id)
        if not category:
            raise NotFoundException("Categoría", category_id)
        self.category_repo.soft_delete(category_id, deleted_by)


def _to_response(c: Category) -> CategoryResponse:
    return CategoryResponse(
        id=c.id,
        nombre=c.nombre,
        descripcion=c.descripcion,
        activa=c.activa,
        created_at=c.created_at,
        updated_at=c.updated_at,
    )
