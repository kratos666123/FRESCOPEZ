from typing import Optional
from math import ceil
from fastapi import APIRouter, Query, Depends

from app.application.dto.delivery_dto import CreateDeliveryRequest, UpdateDeliveryRequest, DeliveryResponse
from app.application.use_cases.deliveries.delivery_use_cases import (
    CreateDeliveryUseCase,
    GetDeliveryUseCase,
    ListDeliveriesUseCase,
    UpdateDeliveryUseCase,
    DeleteDeliveryUseCase,
)
from app.infrastructure.database.repositories.delivery_repository_impl import DeliveryRepositoryImpl
from app.infrastructure.database.repositories.product_repository_impl import ProductRepositoryImpl
from app.infrastructure.database.repositories.user_repository_impl import UserRepositoryImpl
from app.infrastructure.database.repositories.vehicle_repository_impl import VehicleRepositoryImpl
from app.presentation.api.dependencies.auth_dependencies import CurrentUser, require_roles
from app.presentation.api.dependencies.db_dependencies import DbSession
from app.shared.responses.api_response import ApiResponse, PaginatedResponse
from app.shared.constants.roles import UserRole, DeliveryType, DeliveryStatus

router = APIRouter(prefix="/entregas", tags=["Entregas"])

# Admin y Empleado crean; repartidor solo actualiza estado
_can_create = Depends(require_roles(UserRole.ADMIN, UserRole.EMPLEADO))
_can_read = Depends(require_roles(UserRole.ADMIN, UserRole.REPARTIDOR, UserRole.EMPLEADO))
_can_update = Depends(require_roles(UserRole.ADMIN, UserRole.REPARTIDOR, UserRole.EMPLEADO))
_can_delete = Depends(require_roles(UserRole.ADMIN))


@router.post(
    "",
    response_model=ApiResponse[DeliveryResponse],
    status_code=201,
    summary="Crear entrega (Admin / Empleado)",
    description=(
        "Registra una entrega. Solo Admin y Empleado pueden crear. "
        "Tipo **compra**: empresa recibe mercancía del proveedor — el stock aumenta al COMPLETAR. "
        "Tipo **venta**: empresa entrega al cliente — el stock disminuye al COMPLETAR. "
        "El vehículo es OBLIGATORIO y debe tener capacidad suficiente. "
        "Estado inicial: PENDIENTE."
    ),
    dependencies=[_can_create],
)
def create_delivery(request: CreateDeliveryRequest, current_user: CurrentUser, db: DbSession):
    delivery_repo = DeliveryRepositoryImpl(db)
    product_repo = ProductRepositoryImpl(db)
    user_repo = UserRepositoryImpl(db)
    vehicle_repo = VehicleRepositoryImpl(db)
    result = CreateDeliveryUseCase(delivery_repo, product_repo, user_repo, vehicle_repo).execute(
        request, created_by=current_user.id, creator_role=current_user.role
    )
    return ApiResponse.created(data=result, message="Entrega registrada exitosamente.")


@router.get(
    "",
    response_model=PaginatedResponse[DeliveryResponse],
    summary="Listar entregas",
    description=(
        "Admin/Empleado: ven todas las entregas. "
        "Repartidor: solo ve las entregas que tiene asignadas."
    ),
    dependencies=[_can_read],
)
def list_deliveries(
    current_user: CurrentUser,
    db: DbSession,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    tipo: Optional[DeliveryType] = Query(None, description="Filtrar por tipo: compra o venta"),
    estado: Optional[DeliveryStatus] = Query(None, description="Filtrar por estado"),
    search: Optional[str] = Query(None, description="Buscar en observaciones"),
):
    delivery_repo = DeliveryRepositoryImpl(db)
    deliveries, total = ListDeliveriesUseCase(delivery_repo).execute(
        page=page,
        page_size=page_size,
        tipo=tipo,
        estado=estado,
        search=search,
        requester_id=current_user.id,
        requester_role=current_user.role,
    )
    return PaginatedResponse(
        data=deliveries, total=total, page=page, page_size=page_size,
        total_pages=ceil(total / page_size) if total else 0,
    )


@router.get(
    "/{delivery_id}",
    response_model=ApiResponse[DeliveryResponse],
    summary="Obtener entrega por ID",
    description=(
        "Admin/Empleado: ven cualquier entrega. "
        "Repartidor: solo ve las que tiene asignadas."
    ),
    dependencies=[_can_read],
)
def get_delivery(delivery_id: int, current_user: CurrentUser, db: DbSession):
    delivery_repo = DeliveryRepositoryImpl(db)
    result = GetDeliveryUseCase(delivery_repo).execute(
        delivery_id, requester_id=current_user.id, requester_role=current_user.role
    )
    return ApiResponse.ok(data=result)


@router.put(
    "/{delivery_id}",
    response_model=ApiResponse[DeliveryResponse],
    summary="Actualizar entrega",
    description=(
        "Admin/Empleado: editan todos los campos. "
        "Repartidor: solo puede actualizar el estado de entregas asignadas a él."
    ),
    dependencies=[_can_update],
)
def update_delivery(
    delivery_id: int, request: UpdateDeliveryRequest, current_user: CurrentUser, db: DbSession
):
    delivery_repo = DeliveryRepositoryImpl(db)
    product_repo = ProductRepositoryImpl(db)
    user_repo = UserRepositoryImpl(db)
    vehicle_repo = VehicleRepositoryImpl(db)
    result = UpdateDeliveryUseCase(delivery_repo, product_repo, user_repo, vehicle_repo).execute(
        delivery_id, request, updated_by=current_user.id, updater_role=current_user.role
    )
    return ApiResponse.ok(data=result, message="Entrega actualizada exitosamente.")


@router.patch(
    "/{delivery_id}",
    response_model=ApiResponse[DeliveryResponse],
    summary="Actualizar parcialmente entrega (PATCH)",
    description=(
        "Admin/Empleado: editan todos los campos. "
        "Repartidor: solo puede actualizar el estado de entregas asignadas a él."
    ),
    dependencies=[_can_update],
)
def patch_delivery(
    delivery_id: int, request: UpdateDeliveryRequest, current_user: CurrentUser, db: DbSession
):
    delivery_repo = DeliveryRepositoryImpl(db)
    product_repo = ProductRepositoryImpl(db)
    user_repo = UserRepositoryImpl(db)
    vehicle_repo = VehicleRepositoryImpl(db)
    result = UpdateDeliveryUseCase(delivery_repo, product_repo, user_repo, vehicle_repo).execute(
        delivery_id, request, updated_by=current_user.id, updater_role=current_user.role
    )
    return ApiResponse.ok(data=result, message="Entrega actualizada exitosamente.")


@router.delete(
    "/{delivery_id}",
    response_model=ApiResponse,
    summary="Eliminar entrega (Admin)",
    description="Solo el administrador puede eliminar (soft delete) un informe de entrega.",
    dependencies=[_can_delete],
)
def delete_delivery(delivery_id: int, current_user: CurrentUser, db: DbSession):
    delivery_repo = DeliveryRepositoryImpl(db)
    vehicle_repo = VehicleRepositoryImpl(db)
    DeleteDeliveryUseCase(delivery_repo, vehicle_repo).execute(
        delivery_id, deleted_by=current_user.id, deleter_role=current_user.role
    )
    return ApiResponse.ok(message="Entrega eliminada exitosamente.")
