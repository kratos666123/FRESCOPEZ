from decimal import Decimal
from app.domain.entities.product import Product
from app.domain.repositories.product_repository import ProductRepository
from app.domain.repositories.category_repository import CategoryRepository
from app.application.dto.product_dto import (
    CreateProductRequest,
    UpdateProductRequest,
    UpdateStockRequest,
    ProductResponse,
    ProductStockResponse,
    StockWeightResponse,
)
from app.shared.exceptions.custom_exceptions import (
    ConflictException,
    NotFoundException,
)
from app.shared.utils.weight_converter import weight_summary


def _to_response(p: Product) -> ProductResponse:
    summary = weight_summary(p.stock_kg)
    return ProductResponse(
        id=p.id,
        categoria_id=p.categoria_id,
        nombre=p.nombre,
        descripcion=p.descripcion,
        precio=p.precio,
        precio_compra_kg=p.precio_compra_kg,
        stock_kg=p.stock_kg,
        stock=StockWeightResponse(**summary),
        imagen=p.imagen,
        activo=p.activo,
        created_at=p.created_at,
        updated_at=p.updated_at,
    )


def _to_stock_response(p: Product) -> ProductStockResponse:
    summary = weight_summary(p.stock_kg)
    return ProductStockResponse(
        id=p.id,
        nombre=p.nombre,
        stock_kg=p.stock_kg,
        stock=StockWeightResponse(**summary),
        activo=p.activo,
    )


class CreateProductUseCase:
    def __init__(self, product_repo: ProductRepository, category_repo: CategoryRepository):
        self.product_repo = product_repo
        self.category_repo = category_repo

    def execute(self, request: CreateProductRequest, created_by: int) -> ProductResponse:
        category = self.category_repo.get_by_id(request.categoria_id)
        if not category:
            raise NotFoundException("Categoría", request.categoria_id)
        if not category.activa:
            raise NotFoundException("Categoría activa", request.categoria_id)

        if self.product_repo.exists_by_nombre(request.nombre):
            raise ConflictException(f"El producto '{request.nombre}' ya existe.")

        product = Product(
            id=0,
            categoria_id=request.categoria_id,
            nombre=request.nombre,
            descripcion=request.descripcion,
            precio=request.precio,
            precio_compra_kg=request.precio_compra_kg,
            stock_kg=request.stock_kg,
            imagen=request.imagen,
            activo=request.activo,
            created_by=created_by,
            updated_by=created_by,
        )
        created = self.product_repo.create(product)
        return _to_response(created)


class GetProductUseCase:
    def __init__(self, product_repo: ProductRepository):
        self.product_repo = product_repo

    def execute(self, product_id: int) -> ProductResponse:
        product = self.product_repo.get_by_id(product_id)
        if not product:
            raise NotFoundException("Producto", product_id)
        return _to_response(product)


class GetProductStockUseCase:
    """Use case for employees: only stock info."""
    def __init__(self, product_repo: ProductRepository):
        self.product_repo = product_repo

    def execute(self, product_id: int) -> ProductStockResponse:
        product = self.product_repo.get_by_id(product_id)
        if not product:
            raise NotFoundException("Producto", product_id)
        return _to_stock_response(product)


class ListProductsUseCase:
    def __init__(self, product_repo: ProductRepository):
        self.product_repo = product_repo

    def execute(
        self,
        page: int = 1,
        page_size: int = 20,
        categoria_id: int | None = None,
        search: str | None = None,
        activo: bool | None = None,
    ) -> tuple[list[ProductResponse], int]:
        products, total = self.product_repo.list(
            page=page, page_size=page_size,
            categoria_id=categoria_id, search=search, activo=activo,
        )
        return [_to_response(p) for p in products], total


class UpdateProductUseCase:
    def __init__(self, product_repo: ProductRepository, category_repo: CategoryRepository):
        self.product_repo = product_repo
        self.category_repo = category_repo

    def execute(
        self, product_id: int, request: UpdateProductRequest, updated_by: int
    ) -> ProductResponse:
        product = self.product_repo.get_by_id(product_id)
        if not product:
            raise NotFoundException("Producto", product_id)

        if request.categoria_id is not None and request.categoria_id != product.categoria_id:
            category = self.category_repo.get_by_id(request.categoria_id)
            if not category or not category.activa:
                raise NotFoundException("Categoría activa", request.categoria_id)
            product.categoria_id = request.categoria_id

        if request.nombre and request.nombre != product.nombre:
            if self.product_repo.exists_by_nombre(request.nombre, exclude_id=product_id):
                raise ConflictException(f"El producto '{request.nombre}' ya existe.")
            product.nombre = request.nombre

        if request.descripcion is not None:
            product.descripcion = request.descripcion
        if request.precio is not None:
            product.precio = request.precio
        if request.precio_compra_kg is not None:
            product.precio_compra_kg = request.precio_compra_kg
        if request.stock_kg is not None:
            product.stock_kg = request.stock_kg
        if request.imagen is not None:
            product.imagen = request.imagen
        if request.activo is not None:
            product.activo = request.activo

        product.updated_by = updated_by
        updated = self.product_repo.update(product)
        return _to_response(updated)


class UpdateStockUseCase:
    """Employee-only: update only the stock_kg of a product."""
    def __init__(self, product_repo: ProductRepository):
        self.product_repo = product_repo

    def execute(
        self, product_id: int, request: UpdateStockRequest, updated_by: int
    ) -> ProductStockResponse:
        product = self.product_repo.get_by_id(product_id)
        if not product:
            raise NotFoundException("Producto", product_id)

        updated = self.product_repo.update_stock(product_id, request.stock_kg, updated_by)
        return _to_stock_response(updated)


class DeleteProductUseCase:
    def __init__(self, product_repo: ProductRepository):
        self.product_repo = product_repo

    def execute(self, product_id: int, deleted_by: int) -> None:
        product = self.product_repo.get_by_id(product_id)
        if not product:
            raise NotFoundException("Producto", product_id)
        self.product_repo.soft_delete(product_id, deleted_by)
