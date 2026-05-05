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


# ==================== FUNCIONES JWT ====================


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Crea un JWT access token con secret_key uniforme."""
    to_encode = data.copy()
    expire = datetime.now(UTC) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode["exp"] = expire
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict | None:
    """Decodifica un JWT access token con secret_key uniforme."""
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except JWTError as exc:
        logger.debug("Token JWT inválido o expirado: %s", exc)
        return None


# ==================== AUTENTICACIÓN DEMO (ADMIN) ====================


def authenticate_demo_user(username: str, password: str) -> dict | None:
    """Autentica usuarios demo (admin). Devuelve dict con token o None."""
    if username not in USERS_DB:
        logger.warning("Intento de login fallido: usuario '%s' no existe.", username)
        return None
    
    user_info = USERS_DB[username]
    if not bcrypt.checkpw(password.encode(), user_info["hashed_password"].encode()):
        logger.warning("Contraseña incorrecta para el empleado: %s", username)
        return None
    
    # Generar token con sub=username y role=admin
    token = create_access_token({"sub": user_info["username"], "role": user_info["role"]})
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60,
    }


# ==================== AUTENTICACIÓN USUARIOS REGISTRADOS ====================


async def authenticate_registered_user(db: AsyncSession, email: str, password: str) -> UserORM | None:
    """Autentica usuarios registrados por email."""
    result = await db.execute(select(UserORM).filter(UserORM.email == email))
    user = result.scalar()
    if user and bcrypt.checkpw(password.encode(), user.password_hash.encode()):
        return user
    return None


async def get_current_registered_user(db: AsyncSession, token: str) -> UserORM | None:
    """Obtiene el usuario registrado actual desde el token (sub=email)."""
    payload = decode_access_token(token)
    if payload is None:
        return None
    
    email: str = payload.get("sub")
    if email is None:
        return None
    
    result = await db.execute(select(UserORM).filter(UserORM.email == email))
    return result.scalar()


# Build USERS_DB from settings at import time (keeps secrets out of source)
try:
    _build_users_db_from_settings()
except Exception:
    logger.exception("Error building USERS_DB from settings")
