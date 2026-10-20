import os
import shutil
from decimal import Decimal
from math import ceil
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile

from app.application.dto.product_dto import (
    CreateProductRequest,
    ProductResponse,
    ProductStockResponse,
    UpdateProductRequest,
    UpdateStockRequest,
)
from app.application.use_cases.products.product_use_cases import (
    CreateProductUseCase,
    DeleteProductUseCase,
    GetProductStockUseCase,
    GetProductUseCase,
    ListProductsUseCase,
    UpdateProductUseCase,
    UpdateStockUseCase,
)
from app.infrastructure.database.repositories.category_repository_impl import CategoryRepositoryImpl
from app.infrastructure.database.repositories.product_repository_impl import ProductRepositoryImpl
from app.presentation.api.dependencies.auth_dependencies import AdminUser, CurrentUser, require_roles
from app.presentation.api.dependencies.db_dependencies import DbSession
from app.shared.constants.roles import UserRole
from app.shared.responses.api_response import ApiResponse, PaginatedResponse
from app.domain.entities.user import User

router = APIRouter(prefix="/productos", tags=["Productos"])

class ProductFormData:
    def __init__(
        self,
        nombre: str = Form(...),
        categoria_id: int = Form(...),
        precio: str = Form(...),
        precio_compra_kg: str = Form("0"),
        stock_kg: str = Form(...),
        descripcion: Optional[str] = Form(None),
        activo: bool = Form(True),
        imagen: Optional[UploadFile] = File(None)
    ):
        self.nombre = nombre
        self.categoria_id = categoria_id

        def limpiar_numero(valor: str) -> Decimal:
            if not valor or str(valor).strip().lower() in ("", "null", "undefined"):
                return Decimal("0")
            valor_limpio = str(valor).replace(",", ".")
            try:
                return Decimal(valor_limpio)
            except Exception:
                return Decimal("0")

        self.precio = limpiar_numero(precio)
        self.precio_compra_kg = limpiar_numero(precio_compra_kg)
        self.stock_kg = limpiar_numero(stock_kg)
        self.descripcion = descripcion
        self.activo = activo
        self.imagen = imagen

@router.post("", response_model=ApiResponse)
def create_product(
    current_user: AdminUser, # Se exige explícitamente que sea Admin
    db: DbSession,           # Usando el alias limpio que ya tenías
    form: ProductFormData = Depends()
):
    # Lógica de archivo
    ruta_imagen = None
    if form.imagen:
        upload_dir = "static/products"
        os.makedirs(upload_dir, exist_ok=True)
        ruta_imagen = f"{upload_dir}/{form.imagen.filename}"
        with open(ruta_imagen, "wb") as buffer:
            shutil.copyfileobj(form.imagen.file, buffer)

    # Construcción del DTO original
    request = CreateProductRequest(
        nombre=form.nombre,
        categoria_id=form.categoria_id,
        precio=form.precio,
        precio_compra_kg=form.precio_compra_kg,
        stock_kg=form.stock_kg,
        descripcion=form.descripcion,
        imagen=ruta_imagen,
        activo=form.activo
    )
    
    product_repo = ProductRepositoryImpl(db)
    category_repo = CategoryRepositoryImpl(db)
    result = CreateProductUseCase(product_repo, category_repo).execute(request, created_by=current_user.id)
    
    # Eliminé el segundo return estorbo que tenías abajo
    return ApiResponse.created(data=result, message="Producto creado exitosamente.")


@router.get(
    "",
    response_model=PaginatedResponse[ProductResponse],
    summary="Listar productos (Admin)",
    description="Lista paginada de productos con stock en todas las unidades (kg, lb, ton, oz).",
    dependencies=[Depends(require_roles([UserRole.ADMIN, UserRole.REPARTIDOR, UserRole.EMPLEADO]))],
)
def list_products(
    current_user: CurrentUser,
    db: DbSession,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    categoria_id: Optional[int] = Query(None, description="Filtrar por categoría"),
    search: Optional[str] = Query(None, description="Buscar por nombre o descripción"),
    activo: Optional[bool] = Query(None),
):
    repo = ProductRepositoryImpl(db)
    products, total = ListProductsUseCase(repo).execute(
        page=page, page_size=page_size, categoria_id=categoria_id, search=search, activo=activo
    )
    return PaginatedResponse(
        data=products, total=total, page=page, page_size=page_size,
        total_pages=ceil(total / page_size) if total else 0,
    )


@router.get(
    "/{product_id}",
    summary="Obtener producto (Admin o Empleado)",
    description=(
        "Admin recibe información completa. "
        "Empleado solo recibe información de stock (en kg, lb, ton, oz)."
    ),
)
def get_product(
    product_id: int,
    current_user: CurrentUser,
    db: DbSession,
):
    product_repo = ProductRepositoryImpl(db)
    if current_user.role == UserRole.EMPLEADO:
        result = GetProductStockUseCase(product_repo).execute(product_id)
        return ApiResponse[ProductStockResponse].ok(data=result)
        
    result = GetProductUseCase(product_repo).execute(product_id)
    return ApiResponse[ProductResponse].ok(data=result)


@router.put("/{product_id}", dependencies=[Depends(require_roles(UserRole.ADMIN))])
def update_product(
    product_id: int,
    current_user: AdminUser,
    db: DbSession,
    nombre: Optional[str] = Form(None),
    categoria_id: Optional[int] = Form(None),
    precio: Optional[float] = Form(None),
    precio_compra_kg: Optional[float] = Form(None),
    stock_kg: Optional[float] = Form(None),
    descripcion: Optional[str] = Form(None),
    activo: Optional[bool] = Form(None),
    imagen: Optional[UploadFile] = File(None)
):
    product_repo = ProductRepositoryImpl(db)

    ruta_imagen = None
    if imagen:
        upload_dir = "static/products"
        os.makedirs(upload_dir, exist_ok=True)
        ruta_imagen = f"{upload_dir}/{imagen.filename}"
        with open(ruta_imagen, "wb") as buffer:
            shutil.copyfileobj(imagen.file, buffer)

    full_request = UpdateProductRequest(
        nombre=nombre,
        categoria_id=categoria_id,
        precio=Decimal(str(precio)) if precio is not None else None,
        precio_compra_kg=Decimal(str(precio_compra_kg)) if precio_compra_kg is not None else None,
        stock_kg=Decimal(str(stock_kg)) if stock_kg is not None else None,
        descripcion=descripcion,
        activo=activo,
        imagen=ruta_imagen
    )

    category_repo = CategoryRepositoryImpl(db)
    result = UpdateProductUseCase(product_repo, category_repo).execute(product_id, full_request, updated_by=current_user.id)
    return ApiResponse.ok(data=result, message="Producto actualizado exitosamente.")


@router.patch(
    "/{product_id}/stock",
    response_model=ApiResponse[ProductStockResponse],
    summary="Actualizar stock del producto (Empleado o Admin)",
    description="Endpoint dedicado para que el empleado actualice únicamente el stock.",
    dependencies=[Depends(require_roles(UserRole.ADMIN, UserRole.EMPLEADO))],
)
def update_stock(product_id: int, request: UpdateStockRequest, current_user: CurrentUser, db: DbSession):
    product_repo = ProductRepositoryImpl(db)
    result = UpdateStockUseCase(product_repo).execute(product_id, request, updated_by=current_user.id)
    return ApiResponse.ok(data=result, message="Stock actualizado exitosamente.")


@router.delete(
    "/{product_id}",
    response_model=ApiResponse,
    summary="Eliminar producto (Admin)",
    dependencies=[Depends(require_roles(UserRole.ADMIN))],
)
def delete_product(product_id: int, current_user: AdminUser, db: DbSession):
    product_repo = ProductRepositoryImpl(db)
    DeleteProductUseCase(product_repo).execute(product_id, deleted_by=current_user.id)
    return ApiResponse.ok(message="Producto eliminado exitosamente.")