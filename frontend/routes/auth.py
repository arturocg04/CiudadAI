from pathlib import Path

from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from httpx import HTTPStatusError, RequestError

from services.api_client import api_client

router = APIRouter()
templates = Jinja2Templates(
    directory=str(Path(__file__).resolve().parent.parent / "templates")
)


@router.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse(
        request, "login.html", {"request": request, "error": None}
    )


@router.post("/login")
async def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    try:
        token_response = await api_client.login(username=username, password=password)
    except HTTPStatusError:
        return templates.TemplateResponse(
            request,
            "login.html",
            {"request": request, "error": "Credenciales inválidas."},
            status_code=401,
        )
    except RequestError:
        return templates.TemplateResponse(
            request,
            "login.html",
            {"request": request, "error": "No se pudo conectar con la API."},
            status_code=503,
        )

    # Obtener información del usuario actual
    try:
        user = await api_client.me(token_response.access_token)
    except (HTTPStatusError, RequestError):
        return templates.TemplateResponse(
            request,
            "login.html",
            {
                "request": request,
                "error": "No se pudo obtener la información del usuario.",
            },
            status_code=503,
        )

    request.session["access_token"] = token_response.access_token
    request.session["role"] = user.role
    request.session["username"] = user.username

    # Redirigir según el rol del usuario
    if user.role == "admin":
        return RedirectResponse(url="/admin/dashboard", status_code=303)
    else:
        return RedirectResponse(url="/citizen/dashboard", status_code=303)


@router.post("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)
