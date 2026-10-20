from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.application.dto.auth_dto import LoginRequest, TokenResponse, RefreshTokenRequest
from app.application.use_cases.auth.login_use_case import LoginUseCase
from app.infrastructure.database.repositories.user_repository_impl import UserRepositoryImpl
from app.infrastructure.security.jwt_handler import decode_token, create_access_token, get_token_expiry_seconds
from app.infrastructure.database.models.token_model import RefreshTokenModel
from app.presentation.api.dependencies.db_dependencies import DbSession
from app.shared.responses.api_response import ApiResponse
from app.shared.exceptions.custom_exceptions import UnauthorizedException
from sqlalchemy import select
from datetime import datetime, timezone

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post(
    "/login",
    response_model=ApiResponse[TokenResponse],
    summary="Iniciar sesión",
    description="Autentica al usuario con nombre de usuario y contraseña. Devuelve access token y refresh token.",
)
def login(request: LoginRequest, db: DbSession):
    user_repo = UserRepositoryImpl(db)
    use_case = LoginUseCase(user_repo=user_repo, db=db)
    token_data = use_case.execute(request)
    user = user_repo.get_by_username(request.username)
    data_response = token_data.dict()
    data_response["nombre"] = user.nombre
    return ApiResponse.ok(data=token_data, message="Inicio de sesión exitoso.")


@router.post(
    "/refresh",
    response_model=ApiResponse[TokenResponse],
    summary="Renovar access token",
    description="Usa el refresh token para obtener un nuevo access token sin volver a autenticarse.",
)
def refresh_token(request: RefreshTokenRequest, db: DbSession):
    payload = decode_token(request.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise UnauthorizedException("Refresh token inválido o expirado.")

    # Check DB that token is not revoked
    stmt = select(RefreshTokenModel).where(
        RefreshTokenModel.token == request.refresh_token,
        RefreshTokenModel.is_revoked == False,  # noqa: E712
        RefreshTokenModel.expires_at > datetime.now(timezone.utc),
    )
    db_token = db.execute(stmt).scalar_one_or_none()
    if not db_token:
        raise UnauthorizedException("Refresh token inválido, revocado o expirado.")

    # Revoke old token and issue new pair
    db_token.is_revoked = True
    db.commit()

    new_payload = {
        "sub": payload["sub"],
        "username": payload["username"],
        "role": payload["role"],
    }
    access_token = create_access_token(new_payload)

    from app.infrastructure.security.jwt_handler import create_refresh_token
    from datetime import timedelta
    new_refresh = create_refresh_token(new_payload)
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    db.add(RefreshTokenModel(
        user_id=db_token.user_id,
        token=new_refresh,
        expires_at=expires_at,
        is_revoked=False,
    ))
    db.commit()

    token_data = TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh,
        token_type="bearer",
        expires_in=get_token_expiry_seconds("access"),
    )
    return ApiResponse.ok(data=token_data, message="Token renovado exitosamente.")


@router.post(
    "/logout",
    response_model=ApiResponse,
    summary="Cerrar sesión",
    description="Revoca el refresh token actual del usuario.",
)
def logout(request: RefreshTokenRequest, db: DbSession):
    stmt = select(RefreshTokenModel).where(
        RefreshTokenModel.token == request.refresh_token,
        RefreshTokenModel.is_revoked == False,  # noqa: E712
    )
    db_token = db.execute(stmt).scalar_one_or_none()
    if db_token:
        db_token.is_revoked = True
        db.commit()
    return ApiResponse.ok(message="Sesión cerrada exitosamente.")
