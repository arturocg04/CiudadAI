from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from config import settings

# from routes.auth import router as auth_router  # DEPRECATED: Using pages.py instead
from routes.pages import router as pages_router

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
