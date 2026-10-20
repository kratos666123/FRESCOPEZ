from abc import ABC, abstractmethod
from typing import Optional
from app.domain.entities.category import Category


class CategoryRepository(ABC):

    @abstractmethod
    def create(self, category: Category) -> Category: ...

    @abstractmethod
    def get_by_id(self, category_id: int) -> Optional[Category]: ...

    @abstractmethod
    def list(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        activa: Optional[bool] = None,
    ) -> tuple[list[Category], int]: ...

    @abstractmethod
    def update(self, category: Category) -> Category: ...

    @abstractmethod
    def soft_delete(self, category_id: int, deleted_by: int) -> bool: ...

    @abstractmethod
    def exists_by_nombre(self, nombre: str, exclude_id: Optional[int] = None) -> bool: ...
