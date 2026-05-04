"""Punto de entrada principal de la API.

Propósito: crear la aplicación FastAPI, registrar middlewares, handlers y routers.
Ejemplo de uso: ejecutar `uvicorn src.app:app --reload` para arrancar el servicio.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from src.config import settings
from src.db.init_db import init_db
from src.middleware import register_middlewares
from src.models.errors import AuthenticationError, ErrorResponse
from src.routers.admin_router import admin_router
from src.routers.auth_router import auth_router
from src.routers.citizen_router import citizen_router
from src.routers.health_router import health_router
from src.routers.items_router import items_router
from src.routers.tickets_router import tickets_router
from src.routers.user_router import router as user_router

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestiona inicio y apagado del servicio.

    Crea las tablas de BD al arrancar si no existen.
    """

    logger.info("Iniciando CiudadAI API...")
    await init_db()
    yield
    logger.info("Apagando CiudadAI API.")


app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
    docs_url=settings.docs_url,
    openapi_url=settings.openapi_url,
    redoc_url=settings.redoc_url,
    lifespan=lifespan,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponse},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": ErrorResponse},
    },
)

# Middlewares HTTP transversales (CORS, trazabilidad, etc.).
register_middlewares(app)


@app.exception_handler(AuthenticationError)
async def authentication_exception_handler(
    request: Request,
    exc: AuthenticationError,
) -> JSONResponse:
    """Traduce errores de autenticación a una respuesta HTTP 401."""

    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": str(exc)},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handler genérico para errores no controlados.

    Mantiene un formato estable para el cliente incluso ante fallos inesperados.
    """

    logger.exception("Error no controlado en la API: %s", exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Se produjo un error interno no controlado."},
    )


# Registro de routers bajo un prefijo de versión para mantener compatibilidad futura.
app.include_router(health_router, prefix=settings.api_prefix)
app.include_router(auth_router, prefix=settings.api_prefix)
app.include_router(user_router, prefix=f"{settings.api_prefix}/user")
app.include_router(admin_router, prefix=settings.api_prefix)
app.include_router(citizen_router, prefix=settings.api_prefix)
app.include_router(items_router, prefix=settings.api_prefix)
app.include_router(tickets_router, prefix=settings.api_prefix)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.app:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=True,
    )
