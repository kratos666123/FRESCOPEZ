from abc import ABC, abstractmethod
from typing import Optional
from app.domain.entities.user import User
from app.shared.constants.roles import UserRole


class UserRepository(ABC):

    @abstractmethod
    def create(self, user: User) -> User: ...

    @abstractmethod
    def get_by_id(self, user_id: int) -> Optional[User]: ...

    @abstractmethod
    def get_by_username(self, username: str) -> Optional[User]: ...

    @abstractmethod
    def get_by_documento(self, documento: str) -> Optional[User]: ...

    @abstractmethod
    def get_by_correo(self, correo: str) -> Optional[User]: ...

    @abstractmethod
    def list(
        self,
        page: int = 1,
        page_size: int = 20,
        role: Optional[UserRole] = None,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> tuple[list[User], int]: ...

    @abstractmethod
    def update(self, user: User) -> User: ...

    @abstractmethod
    def soft_delete(self, user_id: int, deleted_by: int) -> bool: ...

    @abstractmethod
    def exists_by_username(self, username: str, exclude_id: Optional[int] = None) -> bool: ...

    @abstractmethod
    def exists_by_correo(self, correo: str, exclude_id: Optional[int] = None) -> bool: ...

    @abstractmethod
    def exists_by_documento(self, documento: str, exclude_id: Optional[int] = None) -> bool: ...

    @abstractmethod
    def get_by_id_including_deleted(self, user_id: int): ...

    @abstractmethod
    def reactivate(self, user_id: int, updated_by: int): ...

    @abstractmethod
    def hard_delete(self, user_id: int) -> None: ...
