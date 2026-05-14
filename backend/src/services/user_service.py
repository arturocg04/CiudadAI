"""Servicio para gestión de usuarios registrados.

Propósito: manejar registro, login y autenticación de usuarios ciudadanos.
"""

import logging
from datetime import UTC, datetime, timedelta

import bcrypt
from jose import JWTError, jwt
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.db.models import UserORM
from src.models.auth import CurrentUser, UserCreate, UserLogin

logger = logging.getLogger(__name__)


async def register_user(db: AsyncSession, user_data: UserCreate) -> UserORM:
    """Registra un nuevo usuario verificando unicidad de email, teléfono y NIF."""
    # Verificar si email ya existe
    existing_email = await db.execute(
        select(UserORM).filter(UserORM.email == user_data.email)
    )
    if existing_email.scalar():
        raise ValueError("El email ya está registrado.")

    # Verificar si teléfono ya existe
    existing_phone = await db.execute(
        select(UserORM).filter(UserORM.telefono == user_data.telefono)
    )
    if existing_phone.scalar():
        raise ValueError("El teléfono ya está registrado.")

    # Verificar si NIF ya existe
    existing_nif = await db.execute(
        select(UserORM).filter(UserORM.nif == user_data.nif)
    )
    if existing_nif.scalar():
        raise ValueError("El NIF/NIE ya está registrado.")

    # Hash de la contraseña
    hashed_password = bcrypt.hashpw(
        user_data.password.encode(), bcrypt.gensalt()
    ).decode()

    # Crear usuario
    new_user = UserORM(
        nombre=user_data.nombre,
        apellidos=user_data.apellidos,
        nif=user_data.nif,
        telefono=user_data.telefono,
        email=user_data.email,
        domicilio=user_data.domicilio,
        password_hash=hashed_password,
        role="citizen",
    )
    db.add(new_user)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        error_msg = str(exc.orig) if exc.orig else str(exc)
        if "nif" in error_msg.lower():
            raise ValueError("El NIF/NIE ya está registrado.") from exc
        if "email" in error_msg.lower():
            raise ValueError("El email ya está registrado.") from exc
        if "telefono" in error_msg.lower():
            raise ValueError("El teléfono ya está registrado.") from exc
        raise ValueError("Los datos proporcionados ya están registrados.") from exc
    await db.refresh(new_user)
    return new_user


async def authenticate_user(db: AsyncSession, login_data: UserLogin) -> UserORM | None:
    """Autentica un usuario por email y contraseña."""
    result = await db.execute(select(UserORM).filter(UserORM.email == login_data.email))
    user = result.scalar()
    if user and bcrypt.checkpw(
        login_data.password.encode(), user.password_hash.encode()
    ):
        return user
    return None


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Crea un JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=30)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )
    return encoded_jwt


async def get_current_user_from_token(
    db: AsyncSession, token: str
) -> CurrentUser | None:
    """Decodifica el token y obtiene el usuario actual."""
    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        email: str = payload.get("sub")
        if email is None:
            return None
        result = await db.execute(select(UserORM).filter(UserORM.email == email))
        user = result.scalar()
        if user:
            return CurrentUser(
                id=user.id,
                username=user.email,
                role=user.role,
                nombre=user.nombre,
                apellidos=user.apellidos,
                email=user.email,
            )
    except JWTError:
        return None
    return None
