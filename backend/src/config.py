"""Configuración central de la aplicación.

Propósito: leer variables de entorno con Pydantic Settings y ofrecer un objeto único de configuración.
Ejemplo de uso: importar settings desde cualquier módulo para evitar valores hardcoded.
"""

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

from src import __description__, __title__, __version__


class Settings(BaseSettings):
    """Valores de configuración de la API.

    Esta clase carga opciones desde .env y permite cambiar comportamiento sin tocar código.
    """

    # extra=ignore permite que el .env tenga variables adicionales sin romper la carga.
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = Field(default=__title__, alias="APP_NAME")
    app_version: str = Field(default=__version__, alias="APP_VERSION")
    app_description: str = Field(default=__description__, alias="APP_DESCRIPTION")
    app_env: str = Field(default="dev", alias="APP_ENV")
    app_host: str = Field(default="127.0.0.1", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")
    docs_url: str | None = Field(default="/docs", alias="DOCS_URL")
    openapi_url: str | None = Field(default="/openapi.json", alias="OPENAPI_URL")
    redoc_url: str | None = Field(default="/redoc", alias="REDOC_URL")
    api_prefix: str = Field(default="/api/v1", alias="API_PREFIX")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    cors_allow_origins: str = Field(default="*", alias="CORS_ALLOW_ORIGINS")
    access_token_expire_minutes: int = Field(
        default=30,
        alias="ACCESS_TOKEN_EXPIRE_MINUTES",
    )

    # --- Autenticación JWT real ---
    secret_key: str | None = Field(
        default=None,
        alias="SECRET_KEY",
    )
    jwt_secret_key: str | None = Field(
        default=None,
        alias="JWT_SECRET_KEY",
    )
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")

    # --- Credenciales hardcoded (mock de usuarios) ---
    # Usuarios gestionados en auth_service.py con hashes bcrypt.
    mock_auth_username: str | None = Field(default=None, alias="MOCK_AUTH_USERNAME")
    mock_auth_password: str | None = Field(default=None, alias="MOCK_AUTH_PASSWORD")
    mock_auth_token: str | None = Field(default=None, alias="MOCK_AUTH_TOKEN")

    # --- Base de datos PostgreSQL ---
    db_host: str = Field(default="localhost", alias="DB_HOST")
    db_port: int = Field(default=5432, alias="DB_PORT")
    db_name: str = Field(default="ciudadia", alias="DB_NAME")
    db_user: str = Field(default="ciudadia_user", alias="DB_USER")
    db_password: str | None = Field(default=None, alias="DB_PASSWORD")

    @computed_field  # type: ignore[prop-decorator]
    @property
    def database_url(self) -> str:
        """URL de conexión async para SQLAlchemy + asyncpg."""
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    # --- Servicio de inferencia ML ---
    ml_service_url: str = Field(
        default="http://ml_service:8001",
        alias="ML_SERVICE_URL",
    )
    ml_service_timeout: float = Field(default=10.0, alias="ML_SERVICE_TIMEOUT")


settings = Settings()

# Runtime checks: warn or generate safe defaults for development, but avoid hardcoding secrets.
if settings.secret_key is None:
    # In dev, generate a secure key to avoid using a fixed value in code; in prod require explicit config.
    if settings.app_env == "dev":
        import logging
        import secrets

        logging.getLogger(__name__).warning(
            "SECRET_KEY not set in environment; generating ephemeral secret for dev. Set SECRET_KEY in production."
        )
        settings.secret_key = secrets.token_hex(32)
    else:
        raise ValueError(
            "SECRET_KEY must be set in environment for non-dev environments"
        )

if settings.jwt_secret_key is None:
    settings.jwt_secret_key = settings.secret_key

if settings.mock_auth_username and settings.mock_auth_password:
    # sensible to log that demo credentials are active (no password value printed)
    import logging

    logging.getLogger(__name__).warning(
        "Demo mock auth enabled for user '%s' (password taken from env). Remove in production.",
        settings.mock_auth_username,
    )

if settings.db_password is None:
    import logging

    logging.getLogger(__name__).warning(
        "DB_PASSWORD not set; database connections may fail. Provide DB_PASSWORD via environment or Docker secrets."
    )
