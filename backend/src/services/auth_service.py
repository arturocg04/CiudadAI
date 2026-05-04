"""Servicio de autenticación exclusivo para Empleados Municipales.

Propósito: Validar credenciales de empleados, generar tokens JWT firmados
y proteger las rutas de gestión administrativa. Los ciudadanos no utilizan
este servicio ya que interactúan de forma anónima.
"""

import logging
from datetime import UTC, datetime, timedelta

import bcrypt
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.db.models import UserORM

logger = logging.getLogger(__name__)

# Users database: build at startup from configuration to avoid hardcoding secrets in code.
USERS_DB: dict[str, dict] = {}


def _build_users_db_from_settings() -> None:
    """Create USERS_DB from `settings.mock_auth_username` and `settings.mock_auth_password`.

    If the provided password looks like a bcrypt hash (starts with $2b$), use it as-is.
    Otherwise hash the plaintext at startup (keeps only in-memory hash; do not commit plaintext).
    """
    import logging

    from src.config import settings

    if not settings.mock_auth_username or not settings.mock_auth_password:
        if settings.app_env == "dev":
            logging.getLogger(__name__).warning(
                "No se han configurado credenciales de mock para admin. Usando credenciales de desarrollo por defecto."
            )
            username = "api_user"
            pwd = "change_me"
        else:
            logging.getLogger(__name__).debug("No demo mock auth configured via settings.")
            return
    else:
        username = settings.mock_auth_username
        pwd = settings.mock_auth_password
    if pwd.startswith("$2b$"):
        hashed = pwd
    else:
        logging.getLogger(__name__).warning(
            "Mock auth password supplied in environment will be hashed at startup. Do not use real passwords in env in production."
        )
        hashed = bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()

    USERS_DB[username] = {
        "username": username,
        "hashed_password": hashed,
        "role": "admin",
     }


async def authenticate_registered_user(db: AsyncSession, email: str, password: str) -> UserORM | None:
    """Autentica usuarios registrados por email."""
    user_result = await db.execute(select(UserORM).where(UserORM.email == email))
    user = user_result.scalar_one_or_none()
    if user and bcrypt.checkpw(password.encode(), user.password_hash.encode()):
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
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


async def get_current_user(db: AsyncSession, token: str) -> dict | None:
    """Obtiene el usuario actual desde el token (para demo)."""
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        username: str = payload.get("sub")
        if username is None:
            return None
        if username in USERS_DB:
            return {
                "username": username,
                "role": USERS_DB[username]["role"],
            }
    except JWTError:
        return None
    return None


async def get_current_registered_user(db: AsyncSession, token: str) -> UserORM | None:
    """Obtiene el usuario registrado actual desde el token."""
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        email: str = payload.get("sub")
        if email is None:
            return None
        user_result = await db.execute(select(UserORM).where(UserORM.email == email))
        return user_result.scalar_one_or_none()
    except JWTError:
        return None


def decode_access_token(token: str) -> dict | None:
    """Decodifica un JWT access token."""
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError:
        return None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica una contraseña de empleado contra su hash bcrypt."""
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def authenticate_user(username: str, password: str) -> dict | None:
    """Valida credenciales de empleado. Retorna None si fallan."""
    user = USERS_DB.get(username)
    if user is None:
        logger.warning("Intento de login fallido: usuario '%s' no existe.", username)
        return None
    if not verify_password(password, user["hashed_password"]):
        logger.warning("Contraseña incorrecta para el empleado: %s", username)
        return None
    return user


def authenticate_demo_user(username: str, password: str) -> dict | None:
    """Procesa el login y devuelve el token listo para el cliente (Empleado)."""
    user = authenticate_user(username, password)
    if user is None:
        return None
    token = create_access_token({"sub": user["username"], "role": user["role"]})
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60,
    }


# Build USERS_DB from settings at import time (keeps secrets out of source)
try:
    _build_users_db_from_settings()
except Exception:
    logger.exception("Error building USERS_DB from settings")
