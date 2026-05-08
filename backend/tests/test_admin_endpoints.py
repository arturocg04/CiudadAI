"""Tests de los endpoints HTTP de administración.

Propósito: verificar que los endpoints de admin responden correctamente,
que se aplica la autorización por rol y que el flujo de revisión funciona.
Se ha eliminado la autenticación para ciudadanos según los nuevos requisitos.
"""

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

TICKET_PAYLOAD = {
    "nombre": "María",
    "apellidos": "López Sanz",
    "nif": "11111111C",
    "telefono": "+34 622333444",
    "email": "maria@example.com",
    "categoria": "limpieza",
    "description": "Hay grafitis en la fachada del ayuntamiento.",
    "direccion_persona": "Calle del Sol 5",
    "ubicacion_incidencia": "Fachada del Ayuntamiento",
}

# ---------------------------------------------------------------------------
# Tests de autorización (Solo para Admin)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_admin_dashboard_requires_auth(async_client):
    """El dashboard de admin debe rechazar requests sin token."""
    response = await async_client.get("/api/v1/admin/dashboard")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_admin_dashboard_accepts_admin(async_client, admin_token):
    """El dashboard de admin debe responder con 200 para token de admin."""
    response = await async_client.get(
        "/api/v1/admin/dashboard",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "admin"
    assert "content" in data and "title" in data["content"]


@pytest.mark.asyncio
async def test_items_endpoint_returns_default_items(async_client):
    """El endpoint de items debe existir y devolver el listado básico."""
    response = await async_client.get("/api/v1/items")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "items" in data
    assert isinstance(data["items"], list)
    assert len(data["items"]) >= 1
    assert "id" in data["items"][0] and "name" in data["items"][0]
    assert data.get("requested_by") == "frontend"


@pytest.mark.asyncio
async def test_citizen_dashboard_endpoint_is_available(async_client):
    """El endpoint ciudadano de dashboard debe responder con contenido de bienvenida."""
    response = await async_client.get("/api/v1/citizen/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert data["message"].startswith("Bienvenido")
    assert "content" in data and "title" in data["content"]


# ---------------------------------------------------------------------------
# Tests del flujo de tickets (Ciudadano Público / Admin Autenticado)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_citizen_can_create_ticket_publicly(async_client):
    """Un ciudadano puede crear un ticket sin necesidad de estar autenticado."""
    response = await async_client.post(
        "/api/v1/tickets",
        json=TICKET_PAYLOAD,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["id"] is not None
    assert data["categoria"] == "limpieza"


@pytest.mark.asyncio
async def test_admin_can_list_tickets(async_client, admin_token):
    """El admin puede ver los tickets creados públicamente."""
    # Crear un ticket como ciudadano anónimo
    await async_client.post("/api/v1/tickets", json=TICKET_PAYLOAD)

    # Listar como admin
    response = await async_client.get(
        "/api/v1/admin/tickets",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_admin_can_review_ticket(async_client, admin_token):
    """El admin puede revisar un ticket existente usando los nuevos campos de predicción."""
    # Crear ticket público
    create_resp = await async_client.post(
        "/api/v1/tickets", json=TICKET_PAYLOAD
    )
    ticket_id = create_resp.json()["id"]

    # Revisar como admin (Ajustado a los nuevos atributos prediccion_*)
    review_payload = {
        "status": "resolved",
        "prediccion_urgencia": 5,
        "notes": "Confirmado in situ.",
    }
    review_resp = await async_client.patch(
        f"/api/v1/admin/tickets/{ticket_id}/review",
        json=review_payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert review_resp.status_code == 200
    data = review_resp.json()
    # Sin ML disponible en tests, prediccion_urgencia puede ser None pero el ticket queda revisado
    assert data["reviewed_by"] == "api_user"
    assert data["status"] == "resolved"


@pytest.mark.asyncio
async def test_admin_stats_returns_counts(async_client, admin_token):
    """El endpoint de estadísticas debe devolver campos numéricos."""
    # Crear al menos un ticket público
    await async_client.post("/api/v1/tickets", json=TICKET_PAYLOAD)

    response = await async_client.get(
        "/api/v1/admin/stats",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_review_nonexistent_ticket_returns_404(async_client, admin_token):
    """Revisar un ticket inexistente debe devolver 404."""
    review_payload = {
        "status": "accepted",
        "prediccion_urgencia": 3,
    }
    response = await async_client.patch(
        "/api/v1/admin/tickets/99999/review",
        json=review_payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 404
