from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Optional
from app.domain.entities.vehicle import Vehicle


class VehicleRepository(ABC):

    @abstractmethod
    def create(self, vehicle: Vehicle) -> Vehicle: ...

    @abstractmethod
    def get_by_id(self, vehicle_id: int) -> Optional[Vehicle]: ...

    @abstractmethod
    def get_by_placa(self, placa: str) -> Optional[Vehicle]: ...

    @abstractmethod
    def list(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
    ) -> tuple[list[Vehicle], int]: ...

    @abstractmethod
    def update(self, vehicle: Vehicle) -> Vehicle: ...

    @abstractmethod
    def update_carga(self, vehicle_id: int, nueva_carga_kg: Decimal, updated_by: int) -> bool: ...

    @abstractmethod
    def soft_delete(self, vehicle_id: int, deleted_by: int) -> bool: ...
