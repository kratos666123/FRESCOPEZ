from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

# Importaciones de tu app
from app.infrastructure.database.session import get_db
from app.infrastructure.security.jwt_handler import decode_token
from app.infrastructure.database.repositories.user_repository_impl import UserRepositoryImpl
from app.shared.exceptions.custom_exceptions import UnauthorizedException, ForbiddenException
from app.shared.constants.roles import UserRole
from app.domain.entities.user import User

security = HTTPBearer(auto_error=False)

# --- 1. PRIMERO DEFINIMOS TODAS LAS FUNCIONES ---

def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
    db: Session = Depends(get_db),
) -> User:
    if not credentials or not credentials.credentials:
        raise UnauthorizedException("Token de autenticación requerido.")

    payload = decode_token(credentials.credentials)
    if not payload:
        raise UnauthorizedException("Token inválido o expirado.")
    if payload.get("type") != "access":
        raise UnauthorizedException("Se requiere un access token, no un refresh token.")

    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedException("Token malformado.")

    user_repo = UserRepositoryImpl(db)
    user = user_repo.get_by_id(int(user_id))
    if not user or not user.is_active:
        raise UnauthorizedException("Usuario no encontrado o desactivado.")

    return user

def get_current_active_user(current_user: User = Depends(get_current_user)):
    if not getattr(current_user, "is_active", True):
        raise HTTPException(status_code=400, detail="Usuario inactivo")
    return current_user

def require_roles(*roles_or_list):
    """
    Soporta tanto require_roles(Role1, Role2) 
    como require_roles([Role1, Role2]) y compara Enums o strings de forma segura.
    """
    # Si le pasaron una lista como primer argumento, la desempaquetamos
    if len(roles_or_list) == 1 and isinstance(roles_or_list[0], list):
        roles = roles_or_list[0]
    else:
        roles = roles_or_list

    def checker(current_user: User = Depends(get_current_user)) -> User:
        # Normalizamos los roles permitidos a sus valores limpios (string o enum)
        allowed_values = [
            r.value if hasattr(r, "value") else str(r) 
            for r in roles
        ]
        
        # Obtenemos el rol actual del usuario de forma segura
        user_role = (
            current_user.role.value 
            if hasattr(current_user.role, "value") 
            else str(current_user.role)
        )

        if user_role not in allowed_values:
            raise ForbiddenException(
                f"Se requiere uno de los roles: {allowed_values}. "
                f"Tu rol actual es: '{user_role}'."
            )
        return current_user
        
    return checker

def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.ADMIN:
        raise ForbiddenException("Solo el administrador puede realizar esta acción.")
    return current_user

def require_repartidor_or_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in (UserRole.ADMIN, UserRole.REPARTIDOR):
        raise ForbiddenException("Acceso denegado.")
    return current_user

def require_empleado_or_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in (UserRole.ADMIN, UserRole.EMPLEADO):
        raise ForbiddenException("Acceso denegado.")
    return current_user

# --- 2. FINALMENTE CREAMOS LOS ALIAS (DEPENDENCIAS) ---
# Ahora que las funciones ya existen, podemos asignarlas a las variables

CurrentUser = Annotated[User, Depends(get_current_user)]
AdminUser = Annotated[User, Depends(require_admin)]
RepartidorOrAdmin = Annotated[User, Depends(require_repartidor_or_admin)]
EmpleadoOrAdmin = Annotated[User, Depends(require_empleado_or_admin)]