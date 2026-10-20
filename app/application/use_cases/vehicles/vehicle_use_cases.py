from app.domain.entities.vehicle import Vehicle
from app.domain.repositories.vehicle_repository import VehicleRepository
from app.application.dto.vehicle_dto import (
    CreateVehicleRequest,
    UpdateVehicleRequest,
    VehicleResponse,
)
from app.shared.exceptions.custom_exceptions import (
    NotFoundException,
    ConflictException,
    BusinessRuleException,
)
from app.shared.utils.weight_converter import weight_summary
from app.application.dto.product_dto import StockWeightResponse
from decimal import Decimal


def _build_response(vehicle: Vehicle) -> VehicleResponse:
    from app.shared.utils.weight_converter import weight_summary
    from app.application.dto.product_dto import StockWeightResponse
    disponible_kg = max(Decimal("0"), vehicle.capacidad_kg - vehicle.carga_actual_kg)
    return VehicleResponse(
        id=vehicle.id,
        placa=vehicle.placa,
        color=vehicle.color,
        tipo_vehiculo=vehicle.tipo_vehiculo,
        capacidad_kg=vehicle.capacidad_kg,
        carga_actual_kg=vehicle.carga_actual_kg,
        activo=vehicle.activo,
        capacidad=StockWeightResponse(**weight_summary(vehicle.capacidad_kg)),
        carga_actual=StockWeightResponse(**weight_summary(vehicle.carga_actual_kg)),
        disponible=StockWeightResponse(**weight_summary(disponible_kg)),
        created_at=vehicle.created_at,
        updated_at=vehicle.updated_at,
    )


class CreateVehicleUseCase:
    def __init__(self, vehicle_repo: VehicleRepository):
        self.vehicle_repo = vehicle_repo

    def execute(self, request: CreateVehicleRequest, created_by: int) -> VehicleResponse:
        existing = self.vehicle_repo.get_by_placa(request.placa.upper())
        if existing:
            raise ConflictException(f"Ya existe un vehículo con la placa '{request.placa.upper()}'.")

        vehicle = Vehicle(
            id=0,
            placa=request.placa.upper(),
            color=request.color,
            tipo_vehiculo=request.tipo_vehiculo,
            capacidad_kg=request.capacidad_kg,
            carga_actual_kg=Decimal("0"),
            activo=True,
            created_by=created_by,
            updated_by=created_by,
        )
        created = self.vehicle_repo.create(vehicle)
        return _build_response(created)


class GetVehicleUseCase:
    def __init__(self, vehicle_repo: VehicleRepository):
        self.vehicle_repo = vehicle_repo

    def execute(self, vehicle_id: int) -> VehicleResponse:
        vehicle = self.vehicle_repo.get_by_id(vehicle_id)
        if not vehicle:
            raise NotFoundException("Vehículo", vehicle_id)
        return _build_response(vehicle)


class ListVehiclesUseCase:
    def __init__(self, vehicle_repo: VehicleRepository):
        self.vehicle_repo = vehicle_repo

    def execute(
        self,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
    ) -> tuple[list[VehicleResponse], int]:
        vehicles, total = self.vehicle_repo.list(page=page, page_size=page_size, search=search)
        return [_build_response(v) for v in vehicles], total


class UpdateVehicleUseCase:
    def __init__(self, vehicle_repo: VehicleRepository):
        self.vehicle_repo = vehicle_repo

    def execute(self, vehicle_id: int, request: UpdateVehicleRequest, updated_by: int) -> VehicleResponse:
        vehicle = self.vehicle_repo.get_by_id(vehicle_id)
        if not vehicle:
            raise NotFoundException("Vehículo", vehicle_id)

        if request.placa is not None:
            nueva_placa = request.placa.upper()
            if nueva_placa != vehicle.placa:
                existing = self.vehicle_repo.get_by_placa(nueva_placa)
                if existing:
                    raise ConflictException(f"Ya existe un vehículo con la placa '{nueva_placa}'.")
            vehicle.placa = nueva_placa

        if request.color is not None:
            vehicle.color = request.color
        if request.tipo_vehiculo is not None:
            vehicle.tipo_vehiculo = request.tipo_vehiculo
        if request.activo is not None:
            vehicle.activo = request.activo

        if request.capacidad_kg is not None:
            # Validar que la nueva capacidad no sea menor que la carga actual
            if request.capacidad_kg < vehicle.carga_actual_kg:
                raise BusinessRuleException(
                    f"La nueva capacidad ({float(request.capacidad_kg):.2f} kg) no puede ser menor "
                    f"que la carga actual del vehículo ({float(vehicle.carga_actual_kg):.2f} kg)."
                )
            vehicle.capacidad_kg = request.capacidad_kg

        vehicle.updated_by = updated_by
        updated = self.vehicle_repo.update(vehicle)
        return _build_response(updated)


class DeleteVehicleUseCase:
    def __init__(self, vehicle_repo: VehicleRepository):
        self.vehicle_repo = vehicle_repo

    def execute(self, vehicle_id: int, deleted_by: int) -> None:
        vehicle = self.vehicle_repo.get_by_id(vehicle_id)
        if not vehicle:
            raise NotFoundException("Vehículo", vehicle_id)
        if vehicle.carga_actual_kg > Decimal("0"):
            raise BusinessRuleException(
                f"No se puede eliminar el vehículo '{vehicle.placa}' porque tiene "
                f"{float(vehicle.carga_actual_kg):.2f} kg de carga asignada actualmente."
            )
        self.vehicle_repo.soft_delete(vehicle_id, deleted_by)
