from app.domain.repositories.user_repository import UserRepository
from app.infrastructure.security.password_handler import verify_password
from app.infrastructure.security.jwt_handler import (
    create_access_token,
    create_refresh_token,
    get_token_expiry_seconds,
)
from app.application.dto.auth_dto import LoginRequest, TokenResponse
from app.shared.exceptions.custom_exceptions import UnauthorizedException
from app.infrastructure.database.models.token_model import RefreshTokenModel
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone


class LoginUseCase:

    def __init__(self, user_repo: UserRepository, db: Session):
        self.user_repo = user_repo
        self.db = db

    def execute(self, request: LoginRequest) -> TokenResponse:
        user = self.user_repo.get_by_username(request.username)

        if not user:
            raise UnauthorizedException("Usuario o contraseña incorrectos.")

        if not user.is_active:
            raise UnauthorizedException("La cuenta está desactivada. Contacta al administrador.")

        if not verify_password(request.password, user.password_hash):
            raise UnauthorizedException("Usuario o contraseña incorrectos.")

        token_payload = {
            "sub": str(user.id),
            "username": user.username,
            "role": str(user.role),
        }

        access_token = create_access_token(token_payload)
        refresh_token = create_refresh_token(token_payload)

        # Save refresh token
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        rt_model = RefreshTokenModel(
            user_id=user.id,
            token=refresh_token,
            expires_at=expires_at,
            is_revoked=False,
        )
        self.db.add(rt_model)
        self.db.commit()

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=get_token_expiry_seconds("access"),
        )
