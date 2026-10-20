from abc import ABC, abstractmethod
from typing import Optional
from app.domain.entities.user import User


class AuthService(ABC):

    @abstractmethod
    def hash_password(self, plain_password: str) -> str: ...

    @abstractmethod
    def verify_password(self, plain_password: str, hashed_password: str) -> bool: ...

    @abstractmethod
    def create_access_token(self, user: User) -> str: ...

    @abstractmethod
    def create_refresh_token(self, user: User) -> str: ...

    @abstractmethod
    def decode_token(self, token: str) -> Optional[dict]: ...

    @abstractmethod
    def save_refresh_token(self, user_id: int, token: str) -> None: ...

    @abstractmethod
    def revoke_refresh_token(self, token: str) -> None: ...

    @abstractmethod
    def is_refresh_token_valid(self, token: str) -> bool: ...
