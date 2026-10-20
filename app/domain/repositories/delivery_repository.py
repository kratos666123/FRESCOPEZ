from abc import ABC, abstractmethod
from typing import Optional
from app.domain.entities.delivery import Delivery
from app.shared.constants.roles import DeliveryType, DeliveryStatus


class DeliveryRepository(ABC):

    @abstractmethod
    def create(self, delivery: Delivery) -> Delivery: ...

    @abstractmethod
    def get_by_id(self, delivery_id: int) -> Optional[Delivery]: ...

    @abstractmethod
    def list(
        self,
        page: int = 1,
        page_size: int = 20,
        tipo: Optional[DeliveryType] = None,
        estado: Optional[DeliveryStatus] = None,
        id_domiciliario: Optional[int] = None,
        created_by: Optional[int] = None,
        search: Optional[str] = None,
    ) -> tuple[list[Delivery], int]: ...

    @abstractmethod
    def update(self, delivery: Delivery) -> Delivery: ...

    @abstractmethod
    def soft_delete(self, delivery_id: int, deleted_by: int) -> bool: ...
