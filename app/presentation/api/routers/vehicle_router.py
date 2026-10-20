from typing import Optional
from math import ceil
from fastapi import APIRouter, Query, Depends

from app.application.dto.vehicle_dto import CreateVehicleRequest, UpdateVehicleRequest, VehicleResponse
from app.application.use_cases.vehicles.vehicle_use_cases import (
    CreateVehicleUseCase,
    GetVehicleUseCase,
    ListVehiclesUseCase,
    UpdateVehicleUseCase,
    DeleteVehicleUseCase,
)
from app.infrastructure.database.repositories.vehicle_repository_impl import VehicleRepositoryImpl
from app.presentation.api.dependencies.auth_dependencies import CurrentUser, require_roles
from app.presentation.api.dependencies.db_dependencies import DbSession
from app.shared.responses.api_response import ApiResponse, PaginatedResponse
from app.shared.constants.roles import UserRole

router = APIRouter(prefix="/vehiculos", tags=["Vehículos"])

# Solo Admin gestiona vehículos; Admin y Repartidor pueden listar/leer
_admin_only = Depends(require_roles(UserRole.ADMIN))
_can_read = Depends(require_roles(UserRole.ADMIN, UserRole.EMPLEADO, UserRole.REPARTIDOR))


@router.post(
    "",
    response_model=ApiResponse[VehicleResponse],
    status_code=201,
    summary="Crear vehículo (Admin)",
    description="Registra un nuevo vehículo de la flota. Solo el administrador puede hacerlo.",
    dependencies=[_admin_only],
)
def create_vehicle(request: CreateVehicleRequest, current_user: CurrentUser, db: DbSession):
    vehicle_repo = VehicleRepositoryImpl(db)
    result = CreateVehicleUseCase(vehicle_repo).execute(request, created_by=current_user.id)
    return ApiResponse.created(data=result, message="Vehículo registrado exitosamente.")


@router.get(
    "",
    response_model=PaginatedResponse[VehicleResponse],
    summary="Listar vehículos",
    description="Lista todos los vehículos activos de la flota.",
    dependencies=[_can_read],
)
def list_vehicles(
    db: DbSession,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, description="Buscar por placa, tipo o color"),
):
    vehicle_repo = VehicleRepositoryImpl(db)
    vehicles, total = ListVehiclesUseCase(vehicle_repo).execute(
        page=page, page_size=page_size, search=search
    )
    return PaginatedResponse(
        data=vehicles, total=total, page=page, page_size=page_size,
        total_pages=ceil(total / page_size) if total else 0,
    )


@router.get(
    "/{vehicle_id}",
    response_model=ApiResponse[VehicleResponse],
    summary="Obtener vehículo por ID",
    dependencies=[_can_read],
)
def get_vehicle(vehicle_id: int, db: DbSession):
    vehicle_repo = VehicleRepositoryImpl(db)
    result = GetVehicleUseCase(vehicle_repo).execute(vehicle_id)
    return ApiResponse.ok(data=result)


@router.put(
    "/{vehicle_id}",
    response_model=ApiResponse[VehicleResponse],
    summary="Actualizar vehículo (Admin)",
    description="Actualiza los datos de un vehículo. Solo el administrador puede hacerlo.",
    dependencies=[_admin_only],
)
def update_vehicle(vehicle_id: int, request: UpdateVehicleRequest, current_user: CurrentUser, db: DbSession):
    vehicle_repo = VehicleRepositoryImpl(db)
    result = UpdateVehicleUseCase(vehicle_repo).execute(vehicle_id, request, updated_by=current_user.id)
    return ApiResponse.ok(data=result, message="Vehículo actualizado exitosamente.")


@router.delete(
    "/{vehicle_id}",
    response_model=ApiResponse,
    summary="Eliminar vehículo (Admin)",
    description="Soft delete de un vehículo. Solo si no tiene carga activa. Solo Admin.",
    dependencies=[_admin_only],
)
def delete_vehicle(vehicle_id: int, current_user: CurrentUser, db: DbSession):
    vehicle_repo = VehicleRepositoryImpl(db)
    DeleteVehicleUseCase(vehicle_repo).execute(vehicle_id, deleted_by=current_user.id)
    return ApiResponse.ok(message="Vehículo eliminado exitosamente.")
