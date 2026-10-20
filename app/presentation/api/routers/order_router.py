from typing import Optional
from math import ceil
from fastapi import APIRouter, Query, Depends

from app.application.dto.order_dto import CreateOrderRequest, UpdateOrderRequest, OrderResponse
from app.application.use_cases.orders.order_use_cases import (
    CreateOrderUseCase,
    GetOrderUseCase,
    ListOrdersUseCase,
    UpdateOrderUseCase,
    DeleteOrderUseCase,
)
from app.infrastructure.database.repositories.order_repository_impl import OrderRepositoryImpl
from app.infrastructure.database.repositories.user_repository_impl import UserRepositoryImpl
from app.infrastructure.database.repositories.product_repository_impl import ProductRepositoryImpl
from app.infrastructure.database.repositories.vehicle_repository_impl import VehicleRepositoryImpl
from app.presentation.api.dependencies.auth_dependencies import CurrentUser, require_roles
from app.presentation.api.dependencies.db_dependencies import DbSession
from app.shared.responses.api_response import ApiResponse, PaginatedResponse
from app.shared.constants.roles import UserRole, OrderStatus

router = APIRouter(prefix="/pedidos", tags=["Pedidos"])

_all_order_roles = Depends(require_roles(UserRole.ADMIN, UserRole.EMPLEADO, UserRole.REPARTIDOR))
_create_roles = Depends(require_roles(UserRole.ADMIN, UserRole.EMPLEADO))
_delete_roles = Depends(require_roles(UserRole.ADMIN, UserRole.EMPLEADO))


@router.post(
    "",
    response_model=ApiResponse[OrderResponse],
    status_code=201,
    summary="Crear pedido (Admin / Empleado)",
    description=(
        "Crea un pedido de venta. Requiere vehículo con capacidad suficiente. "
        "El vehículo asignado queda con la carga de este pedido hasta que se entregue o cancele."
    ),
    dependencies=[_create_roles],
)
def create_order(request: CreateOrderRequest, current_user: CurrentUser, db: DbSession):
    order_repo = OrderRepositoryImpl(db)
    user_repo = UserRepositoryImpl(db)
    product_repo = ProductRepositoryImpl(db)
    vehicle_repo = VehicleRepositoryImpl(db)
    result = CreateOrderUseCase(order_repo, user_repo, product_repo, vehicle_repo).execute(
        request, created_by=current_user.id
    )
    return ApiResponse.created(data=result, message="Pedido creado exitosamente.")


@router.get(
    "",
    response_model=PaginatedResponse[OrderResponse],
    summary="Listar pedidos",
    dependencies=[_all_order_roles],
)
def list_orders(
    current_user: CurrentUser,
    db: DbSession,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    estado: Optional[OrderStatus] = Query(None),
    id_domiciliario: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
):
    order_repo = OrderRepositoryImpl(db)
    filter_domiciliario = id_domiciliario if current_user.role == UserRole.ADMIN else None
    orders, total = ListOrdersUseCase(order_repo).execute(
        page=page,
        page_size=page_size,
        id_domiciliario=filter_domiciliario,
        estado=estado,
        search=search,
        requester_id=current_user.id,
        requester_role=current_user.role,
    )
    return PaginatedResponse(
        data=orders, total=total, page=page, page_size=page_size,
        total_pages=ceil(total / page_size) if total else 0,
    )


@router.get(
    "/{order_id}",
    response_model=ApiResponse[OrderResponse],
    summary="Obtener pedido por ID",
    dependencies=[_all_order_roles],
)
def get_order(order_id: int, current_user: CurrentUser, db: DbSession):
    order_repo = OrderRepositoryImpl(db)
    result = GetOrderUseCase(order_repo).execute(
        order_id, requester_id=current_user.id, requester_role=current_user.role
    )
    return ApiResponse.ok(data=result)


@router.put(
    "/{order_id}",
    response_model=ApiResponse[OrderResponse],
    summary="Editar pedido",
    dependencies=[_all_order_roles],
)
def update_order(
    order_id: int, request: UpdateOrderRequest, current_user: CurrentUser, db: DbSession
):
    order_repo = OrderRepositoryImpl(db)
    user_repo = UserRepositoryImpl(db)
    product_repo = ProductRepositoryImpl(db)
    vehicle_repo = VehicleRepositoryImpl(db)
    result = UpdateOrderUseCase(order_repo, user_repo, product_repo, vehicle_repo).execute(
        order_id, request, updated_by=current_user.id, updater_role=current_user.role
    )
    return ApiResponse.ok(data=result, message="Pedido actualizado exitosamente.")


@router.patch(
    "/{order_id}",
    response_model=ApiResponse[OrderResponse],
    summary="Actualizar parcialmente pedido (PATCH)",
    dependencies=[_all_order_roles],
)
def patch_order(
    order_id: int, request: UpdateOrderRequest, current_user: CurrentUser, db: DbSession
):
    order_repo = OrderRepositoryImpl(db)
    user_repo = UserRepositoryImpl(db)
    product_repo = ProductRepositoryImpl(db)
    vehicle_repo = VehicleRepositoryImpl(db)
    result = UpdateOrderUseCase(order_repo, user_repo, product_repo, vehicle_repo).execute(
        order_id, request, updated_by=current_user.id, updater_role=current_user.role
    )
    return ApiResponse.ok(data=result, message="Pedido actualizado exitosamente.")


@router.delete(
    "/{order_id}",
    response_model=ApiResponse,
    summary="Cancelar / Eliminar pedido (Admin / Empleado)",
    dependencies=[_delete_roles],
)
def delete_order(order_id: int, current_user: CurrentUser, db: DbSession):
    order_repo = OrderRepositoryImpl(db)
    product_repo = ProductRepositoryImpl(db)
    vehicle_repo = VehicleRepositoryImpl(db)
    DeleteOrderUseCase(order_repo, product_repo, vehicle_repo).execute(
        order_id, deleted_by=current_user.id, deleter_role=current_user.role
    )
    return ApiResponse.ok(message="Pedido cancelado exitosamente.")
