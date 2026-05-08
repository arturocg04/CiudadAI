from pathlib import Path

from frontend.config import settings
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

# from frontend.routes.auth import router as auth_router  # DEPRECATED: Using pages.py instead
from frontend.routes.pages import router as pages_router
from starlette.middleware.sessions import SessionMiddleware

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title=settings.app_name)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
    same_site="lax",
    https_only=False,
)

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
# app.include_router(auth_router)  # DEPRECATED: Using pages.py instead
app.include_router(pages_router)
