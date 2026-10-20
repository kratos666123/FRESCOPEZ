from abc import ABC, abstractmethod
from typing import Optional
from app.domain.entities.order import Order
from app.shared.constants.roles import OrderStatus


class OrderRepository(ABC):

    @abstractmethod
    def create(self, order: Order) -> Order: ...

    @abstractmethod
    def get_by_id(self, order_id: int) -> Optional[Order]: ...

    @abstractmethod
    def list(
        self,
        page: int = 1,
        page_size: int = 20,
        id_domiciliario: Optional[int] = None,
        estado: Optional[OrderStatus] = None,
        search: Optional[str] = None,
        created_by: Optional[int] = None,
    ) -> tuple[list[Order], int]: ...

    @abstractmethod
    def update(self, order: Order) -> Order: ...

    @abstractmethod
    def soft_delete(self, order_id: int, deleted_by: int) -> bool: ...
