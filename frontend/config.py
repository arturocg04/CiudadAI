from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class FrontendSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = Field(default="Frontend FastAPI", alias="FRONTEND_APP_NAME")
    app_env: str = Field(default="dev", alias="FRONTEND_APP_ENV")
    app_host: str = Field(default="0.0.0.0", alias="FRONTEND_APP_HOST")
    app_port: int = Field(default=8500, alias="FRONTEND_APP_PORT")
    backend_base_url: str = Field(
        default="http://127.0.0.1:8000",
        alias="BACKEND_BASE_URL",
    )
    secret_key: str | None = Field(default=None, alias="FRONTEND_SECRET_KEY")


settings = FrontendSettings()
