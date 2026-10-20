from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Optional
from app.domain.entities.product import Product


class ProductRepository(ABC):

    @abstractmethod
    def create(self, product: Product) -> Product: ...

    @abstractmethod
    def get_by_id(self, product_id: int) -> Optional[Product]: ...

    @abstractmethod
    def list(
        self,
        page: int = 1,
        page_size: int = 20,
        categoria_id: Optional[int] = None,
        search: Optional[str] = None,
        activo: Optional[bool] = None,
    ) -> tuple[list[Product], int]: ...

    @abstractmethod
    def update(self, product: Product) -> Product: ...

    @abstractmethod
    def update_stock(self, product_id: int, new_stock_kg: Decimal, updated_by: int) -> Product: ...

    @abstractmethod
    def soft_delete(self, product_id: int, deleted_by: int) -> bool: ...

    @abstractmethod
    def exists_by_nombre(self, nombre: str, exclude_id: Optional[int] = None) -> bool: ...
