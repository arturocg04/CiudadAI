from pathlib import Path
from datetime import datetime, timezone

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from httpx import HTTPStatusError, RequestError

from services.api_client import api_client

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))


def _format_datetime(value: str | datetime | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        dt = value
    else:
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return str(value)
    return dt.strftime("%d/%m/%Y %H:%M")


@router.get("/")
async def home(request: Request):
    if request.session.get("access_token"):
        # Redirigir según rol
        role = request.session.get("role")
        if role == "admin":
            return RedirectResponse(url="/admin/dashboard", status_code=303)
        else:
            return RedirectResponse(url="/citizen/dashboard", status_code=303)

    return templates.TemplateResponse("home.html", {"request": request})


def _translate_api_error(exc: Exception, fallback: str) -> str:
    if isinstance(exc, RequestError):
        return "No se pudo conectar con el backend. Comprueba que el servicio de la API esté en ejecución."

    error_msg = fallback
    if hasattr(exc, "response") and exc.response is not None:
        try:
            error_data = exc.response.json()
            if isinstance(error_data, dict):
                detail = error_data.get("detail") or error_data.get("message")
                if detail:
                    return str(detail)
        except ValueError:
            pass
    return error_msg


@router.get("/register")
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@router.get("/auth/register")
async def auth_register_redirect(request: Request):
    return RedirectResponse(url="/register", status_code=303)


@router.get("/admin/login")
async def admin_login_page(request: Request):
    token = request.session.get("access_token")
    if token:
        try:
            current_user = await api_client.me(token)
            if current_user.role == "admin":
                return RedirectResponse(url="/admin/dashboard", status_code=303)
        except HTTPStatusError:
            pass
    return templates.TemplateResponse("admin_login.html", {"request": request})


@router.get("/auth/login")
async def auth_login_redirect(request: Request):
    return RedirectResponse(url="/", status_code=303)


@router.post("/auth/login")
async def login(request: Request, email: str = Form(...), password: str = Form(...)):
    try:
        token_response = await api_client.login_user(email, password)
        request.session["access_token"] = token_response.access_token

        # Obtener el rol real del usuario a partir del token
        current_user = await api_client.me(token_response.access_token)
        request.session["role"] = current_user.role

        if current_user.role == "admin":
            return RedirectResponse(url="/admin/dashboard", status_code=303)
        return RedirectResponse(url="/citizen/dashboard", status_code=303)
    except (HTTPStatusError, RequestError) as exc:
        error_msg = _translate_api_error(exc, "Credenciales inválidas")
        return templates.TemplateResponse("home.html", {"request": request, "error": error_msg})
    except Exception as exc:
        import logging
        logging.exception(f"Error no controlado en login: {exc}")
        return templates.TemplateResponse("home.html", {"request": request, "error": f"Error interno: {str(exc)}"})


@router.post("/auth/register")
async def register(request: Request, nombre: str = Form(...), apellidos: str = Form(...), nif: str = Form(...), telefono: str = Form(...), email: str = Form(...), domicilio: str = Form(...), password: str = Form(...)):
    try:
        await api_client.register_user(nombre, apellidos, nif, telefono, email, domicilio, password)
        # Auto-login después de registro
        token_response = await api_client.login_user(email, password)
        request.session["access_token"] = token_response.access_token
        request.session["role"] = "citizen"
        return RedirectResponse(url="/citizen/dashboard", status_code=303)
    except (HTTPStatusError, RequestError) as exc:
        error_msg = _translate_api_error(exc, "Error al crear cuenta")
        return templates.TemplateResponse("register.html", {"request": request, "error": error_msg})
    except Exception as exc:
        import logging
        logging.exception(f"Error en registro: {exc}")
        return templates.TemplateResponse("register.html", {"request": request, "error": f"Error interno: {str(exc)}"})


@router.post("/auth/admin/login")
async def admin_login(request: Request, username: str = Form(...), password: str = Form(...)):
    try:
        token_response = await api_client.login_user(username, password)
        current_user = await api_client.me(token_response.access_token)
        if current_user.role != "admin":
            raise HTTPException(status_code=401, detail="Credenciales inválidas.")

        request.session["access_token"] = token_response.access_token
        request.session["role"] = current_user.role
        return RedirectResponse(url="/admin/dashboard", status_code=303)
    except (HTTPStatusError, RequestError) as exc:
        error_msg = _translate_api_error(exc, "Credenciales inválidas")
        return templates.TemplateResponse("admin_login.html", {"request": request, "error": error_msg})
    except HTTPException as exc:
        return templates.TemplateResponse("admin_login.html", {"request": request, "error": str(exc.detail)})


@router.post("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)

    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "ticket_id": ticket_id,
            "search_result": search_result,
            "search_error": search_error,
            "form_error": None,
        },
    )


@router.get("/dashboard")
async def dashboard(request: Request):
    token = request.session.get("access_token")
    if not token:
        return RedirectResponse(url="/login", status_code=303)

    try:
        current_user = await api_client.me(token)
        items = await api_client.items(token)
    except (HTTPStatusError, RequestError):
        request.session.clear()
        return RedirectResponse(url="/login", status_code=303)

    context = {
        "request": request,
        "current_user": current_user,
        "items": items.items,
    }
    return templates.TemplateResponse("dashboard.html", context)


# ============ RUTAS ADMIN ============

@router.get("/admin/dashboard")
async def admin_dashboard(request: Request):
    token = request.session.get("access_token")
    role = request.session.get("role")
    
    if not token or role != "admin":
        return RedirectResponse(url="/admin/login", status_code=303)
    
    try:
        current_user = await api_client.me(token)
        # Llamar al endpoint de admin
        import httpx
        async with httpx.AsyncClient(base_url=api_client.base_url, timeout=10.0) as client:
            dashboard_response = await client.get(
                "/api/v1/admin/dashboard",
                headers={"Authorization": f"Bearer {token}"},
            )
            dashboard_response.raise_for_status()
            admin_data = dashboard_response.json()

            stats_response = await client.get(
                "/api/v1/admin/stats",
                headers={"Authorization": f"Bearer {token}"},
            )
            stats_response.raise_for_status()
            admin_stats = stats_response.json()

            tickets_response = await client.get(
                # Listar todos los tickets creados (sin filtrar por estado)
                "/api/v1/tickets",
                headers={"Authorization": f"Bearer {token}"},
                params={"limit": 10},
            )
            tickets_response.raise_for_status()
            admin_tickets = tickets_response.json()
            for ticket in admin_tickets:
                if ticket and ticket.get("fecha"):
                    ticket["fecha"] = _format_datetime(ticket["fecha"])
    except (HTTPStatusError, RequestError):
        request.session.clear()
        return RedirectResponse(url="/admin/login", status_code=303)
    
    context = {
        "request": request,
        "current_user": current_user,
        "admin_data": admin_data,
        "admin_stats": admin_stats,
        "admin_tickets": admin_tickets,
    }
    return templates.TemplateResponse("admin_dashboard.html", context)


@router.get("/admin/tickets/{ticket_id}")
async def admin_ticket_detail(request: Request, ticket_id: int):
    token = request.session.get("access_token")
    role = request.session.get("role")
    if not token or role != "admin":
        return RedirectResponse(url="/admin/login", status_code=303)

    try:
        import httpx
        async with httpx.AsyncClient(base_url=api_client.base_url, timeout=10.0) as client:
            ticket_response = await client.get(
                f"/api/v1/admin/tickets/{ticket_id}",
                headers={"Authorization": f"Bearer {token}"},
            )
            ticket_response.raise_for_status()
            ticket = ticket_response.json()
            if ticket and ticket.get("fecha"):
                ticket["fecha"] = _format_datetime(ticket["fecha"])

            if ticket and ticket.get("status") == "pending_classification":
                await client.patch(
                    f"/api/v1/admin/tickets/{ticket_id}/review",
                    headers={"Authorization": f"Bearer {token}"},
                    json={"status": "pending_review", "notes": None},
                )
                ticket["status"] = "pending_review"

            spec_response = await client.get("/api/v1/tickets/spec")
            spec_response.raise_for_status()
            spec = spec_response.json()
            statuses = [s for s in (spec.get("statuses") or []) if s in ["pending_review", "resolved"]]
    except HTTPStatusError as exc:
        if exc.response is not None and exc.response.status_code in (401, 403):
            request.session.clear()
            return RedirectResponse(url="/admin/login", status_code=303)
        raise HTTPException(
            status_code=exc.response.status_code if exc.response is not None else 500,
            detail="No se pudo cargar el ticket de administración.",
        )
    except RequestError:
        raise HTTPException(
            status_code=502,
            detail="No se pudo conectar con el backend para obtener el ticket.",
        )

    return templates.TemplateResponse(
        "admin_ticket_edit.html",
        {
            "request": request,
            "ticket": ticket,
            "statuses": statuses,
            "form_error": None,
        },
    )


@router.post("/admin/tickets/{ticket_id}/review")
async def admin_ticket_review_submit(
    request: Request,
    ticket_id: int,
    status: str = Form(...),
    prediccion_urgencia: int = Form(...),
    notes: str = Form(""),
):
    token = request.session.get("access_token")
    role = request.session.get("role")
    if not token or role != "admin":
        return RedirectResponse(url="/admin/login", status_code=303)

    try:
        import httpx
        async with httpx.AsyncClient(base_url=api_client.base_url, timeout=10.0) as client:
            response = await client.patch(
                f"/api/v1/admin/tickets/{ticket_id}/review",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "status": status,
                    "prediccion_urgencia": prediccion_urgencia,
                    "notes": (notes or None),
                },
            )
            response.raise_for_status()
    except HTTPStatusError as exc:
        error_detail = "No se pudo actualizar el ticket."
        try:
            body = exc.response.json()
            if isinstance(body, dict):
                detail = body.get("detail") or body.get("message")
                if detail:
                    error_detail = str(detail)
        except ValueError:
            pass
        # Re-render la pantalla con el error
        try:
            import httpx
            async with httpx.AsyncClient(base_url=api_client.base_url, timeout=10.0) as client:
                ticket_response = await client.get(
                    f"/api/v1/admin/tickets/{ticket_id}",
                    headers={"Authorization": f"Bearer {token}"},
                )
                ticket_response.raise_for_status()
                ticket = ticket_response.json()
                if ticket and ticket.get("fecha"):
                    ticket["fecha"] = _format_datetime(ticket["fecha"])
                spec_response = await client.get("/api/v1/tickets/spec")
                spec_response.raise_for_status()
                statuses = [s for s in (spec_response.json().get("statuses") or []) if s in ["pending_review", "resolved"]]
        except Exception:
            return RedirectResponse(url="/admin/dashboard", status_code=303)

        return templates.TemplateResponse(
            "admin_ticket_edit.html",
            {
                "request": request,
                "ticket": ticket,
                "statuses": statuses,
                "form_error": error_detail,
            },
            status_code=400,
        )
    except RequestError:
        return RedirectResponse(url="/admin/dashboard", status_code=303)

    return RedirectResponse(url="/admin/dashboard", status_code=303)


@router.get("/citizen/report")
async def citizen_report_form(request: Request):
    return RedirectResponse(url="/", status_code=303)


@router.post("/citizen/report")
async def citizen_report_submit(
    request: Request,
    categoria: str = Form(...),
    description: str = Form(...),
    ubicacion_incidencia: str = Form(...),
):
    token = request.session.get("access_token")
    if not token:
        return RedirectResponse(url="/", status_code=303)

    payload = {
        "categoria": categoria,
        "description": description,
        "ubicacion_incidencia": ubicacion_incidencia,
    }
    try:
        ticket = await api_client.create_ticket_authenticated(token, payload)
        return RedirectResponse(url="/citizen/dashboard", status_code=303)
    except HTTPStatusError as exc:
        error_detail = "No se pudo enviar el reporte. Inténtalo de nuevo más tarde."
        try:
            body = exc.response.json()
            if isinstance(body, dict):
                detail = body.get("detail") or body.get("message")
                if detail:
                    error_detail = f"No se pudo enviar el reporte: {detail}"
        except ValueError:
            pass
        # Recargar tickets para mostrar error
        citizen_tickets = []
        try:
            citizen_tickets = await api_client.get_user_tickets(token)
            for ticket in citizen_tickets:
                if ticket.get("fecha"):
                    ticket["fecha"] = _format_datetime(ticket["fecha"])
        except:
            pass
        return templates.TemplateResponse(
            "citizen_dashboard.html",
            {"request": request, "citizen_tickets": citizen_tickets, "form_error": error_detail},
        )
    except RequestError:
        return templates.TemplateResponse(
            "home.html",
            {
                "request": request,
                "ticket_id": None,
                "search_result": None,
                "search_error": None,
                "form_error": "No se pudo conectar con el backend.",
            },
            status_code=503,
        )

    return templates.TemplateResponse(
        "ticket_success.html",
        {"request": request, "ticket": ticket},
    )


# ============ RUTAS CIUDADANO ============

@router.get("/citizen/dashboard")
async def citizen_dashboard(request: Request):
    token = request.session.get("access_token")
    if not token:
        return RedirectResponse(url="/", status_code=303)

    current_user = None
    citizen_tickets = []
    try:
        current_user = await api_client.me(token)
        citizen_tickets = await api_client.get_user_tickets(token)
        # Formatear fechas
        for ticket in citizen_tickets:
            if ticket.get("fecha"):
                ticket["fecha"] = _format_datetime(ticket["fecha"])
    except (HTTPStatusError, RequestError):
        request.session.clear()
        return RedirectResponse(url="/", status_code=303)

    context = {
        "request": request,
        "current_user": current_user,
        "citizen_tickets": citizen_tickets,
    }
    return templates.TemplateResponse("citizen_dashboard.html", context)
