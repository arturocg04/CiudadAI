"""Router de autenticación de ejemplo.

Propósito: mostrar una implementación mínima para login y lectura de usuario actual.
Ejemplo de uso: sirve como puente didáctico antes de pasar a JWT reales u OIDC.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.responses import COMMON_ERROR_RESPONSES
from src.constants import API_TAGS
from src.db.session import get_db
from src.deps import oauth2_scheme
from src.models.auth import CurrentUser, LoginInput, TokenResponse
from src.services.auth_service import (
    authenticate_demo_user,
    decode_access_token,
    get_current_registered_user,
)

auth_router = APIRouter(prefix="/auth", tags=[API_TAGS["auth"]])


@auth_router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
)
async def login(payload: LoginInput) -> TokenResponse:
    """Devuelve un token mock si las credenciales son correctas.

    Este endpoint define el contrato que luego puede mantenerse al migrar a JWT real.
    """

    token_data = authenticate_demo_user(payload.username, payload.password)
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas.",
        )
    return TokenResponse(**token_data)


@auth_router.post(
    "/admin/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
)
async def admin_login(payload: LoginInput) -> TokenResponse:
    """Login para administradores."""

    token_data = authenticate_demo_user(payload.username, payload.password)
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas.",
        )
    return TokenResponse(**token_data)


@auth_router.get(
    "/me",
    response_model=CurrentUser,
    responses=COMMON_ERROR_RESPONSES,
)
async def read_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> CurrentUser:
    """Devuelve el usuario autenticado actual.

    Útil para depurar integración de clientes y validar que el bearer token está llegando correctamente.
    """
    # Primero intentar obtener como usuario registrado
    user = await get_current_registered_user(db, token)
    if user:
        return CurrentUser(
            id=user.id,
            username=user.email,
            role=user.role,
            nombre=user.nombre,
            apellidos=user.apellidos,
            email=user.email,
        )

    # Si no es usuario registrado, usar el método original
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o caducado.",
        )

    username = payload.get("sub")
    role = payload.get("role", "citizen")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido: falta el identificador de usuario.",
        )

    return CurrentUser(id=payload.get("id"), username=username, role=role)
