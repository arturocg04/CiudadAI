"""Router para gestión de usuarios ciudadanos.

Propósito: endpoints para registro y login de usuarios registrados.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.models.auth import TokenResponse, UserCreate, UserLogin
from src.services.auth_service import authenticate_registered_user, create_access_token
from src.services.user_service import register_user

router = APIRouter()


@router.post("/register", response_model=TokenResponse)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Registra un nuevo usuario y devuelve un token de acceso."""
    try:
        user = await register_user(db, user_data)
        access_token = create_access_token(data={"sub": user.email, "role": "citizen"})
        return TokenResponse(
            access_token=access_token, token_type="bearer", expires_in=1800
        )
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err)) from None


@router.post("/login", response_model=TokenResponse)
async def login(login_data: UserLogin, db: AsyncSession = Depends(get_db)):
    """Autentica un usuario registrado y devuelve un token de acceso."""
    user = await authenticate_registered_user(db, login_data.email, login_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    access_token = create_access_token(data={"sub": user.email, "role": user.role})
    return TokenResponse(
        access_token=access_token, token_type="bearer", expires_in=1800
    )
