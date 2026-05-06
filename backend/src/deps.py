"""Dependencias reutilizables de FastAPI.

Propósito: centralizar piezas inyectables como el usuario autenticado actual,
la sesión de BD y los guardas de autorización por rol.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.db.session import get_db
from src.models.auth import CurrentUser
from src.models.errors import AuthenticationError
from src.services.auth_service import (
    decode_access_token,
    get_current_registered_user,
)

# tokenUrl se publica en OpenAPI y debe coincidir con el endpoint de login.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.api_prefix}/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme)) -> CurrentUser:
    """Obtiene el usuario autenticado a partir de un token JWT bearer."""

    payload = decode_access_token(token)
    if payload is None:
        raise AuthenticationError("Token inválido o caducado.")

    username = payload.get("sub")
    role = payload.get("role", "citizen")
    if username is None:
        raise AuthenticationError("Token inválido: falta el identificador de usuario.")

    return CurrentUser(id=payload.get("id"), username=username, role=role)


async def get_current_registered_user_dep(
    db: AsyncSession = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> CurrentUser:
    """Obtiene el usuario registrado autenticado."""
    user = await get_current_registered_user(db, token)
    if user is None:
        raise AuthenticationError("Token inválido o caducado.")
    return CurrentUser(
        id=user.id,
        username=user.email,
        role=user.role,
        nombre=user.nombre,
        apellidos=user.apellidos,
        email=user.email,
    )


def require_admin(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """Dependencia que garantiza que el usuario tiene rol admin.

    Lanza HTTP 403 si el usuario autenticado no es administrador.
    """

    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los administradores pueden acceder a este recurso.",
        )
    return user


# Re-exportar get_db para que los routers puedan importarlo desde deps sin
# conocer la ubicación interna del módulo de base de datos.
__all__ = [
    "get_current_user",
    "get_current_registered_user_dep",
    "require_admin",
    "get_db",
]
