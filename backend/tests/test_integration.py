"""Tests de integración para flujos completos de la aplicación.

Propósito: verificar que los flujos end-to-end funcionan correctamente,
incluyendo anonimización, predicción ML, y revisión por admin.
"""

import pytest

# ---------------------------------------------------------------------------
# Flujos públicos (sin autenticación)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_citizen_can_create_and_admin_can_review_ticket(async_client, admin_token):
    """Flujo completo: ciudadano reporta, admin revisa y clasifica."""

    ticket_payload = {
        "nombre": "Juan",
        "apellidos": "García López",
        "nif": "12345678A",
        "telefono": "+34 666777888",
        "email": "juan@example.com",
        "categoria": "alumbrado_publico",
        "description": "El alumbrado de la calle mayor no funciona.",
        "direccion_persona": "Calle Principal 10",
        "ubicacion_incidencia": "Calle Mayor esquina Plaza",
    }

    # 1. Crear ticket público (ciudadano anónimo)
    create_resp = await async_client.post(
        "/api/v1/tickets",
        json=ticket_payload,
    )
    assert create_resp.status_code == 201
    ticket_data = create_resp.json()
    ticket_id = ticket_data["id"]
    assert ticket_data["status"] == "pending_review"
    assert ticket_data["prediccion_urgencia"] == 3  # Medium (mocked)
    assert ticket_data["prediccion_categoria"] == "limpieza"  # Mocked

    # 2. Admin lista los tickets pendientes de revisión
    list_resp = await async_client.get(
        "/api/v1/admin/tickets?status=pending_review",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert list_resp.status_code == 200
    tickets_list = list_resp.json()
    assert len(tickets_list) > 0
    assert any(t["id"] == ticket_id for t in tickets_list)

    # 3. Admin obtiene los detalles del ticket
    detail_resp = await async_client.get(
        f"/api/v1/admin/tickets/{ticket_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert detail_resp.status_code == 200
    ticket_detail = detail_resp.json()
    assert ticket_detail["id"] == ticket_id
    assert ticket_detail["prediccion_urgencia"] == 3

    # 4. Admin revisa y clasifica el ticket
    review_payload = {
        "status": "accepted",
        "prediccion_urgencia": 4,  # Cambiar a urgencia alta
        "notes": "Confirmado in situ. Necesita reparación urgente.",
    }
    review_resp = await async_client.patch(
        f"/api/v1/admin/tickets/{ticket_id}/review",
        json=review_payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert review_resp.status_code == 200
    reviewed_ticket = review_resp.json()
    assert reviewed_ticket["status"] == "accepted"
    assert reviewed_ticket["prediccion_urgencia"] == 4
    assert reviewed_ticket["reviewed_by"] == "api_user"
    assert reviewed_ticket["admin_notes"] == "Confirmado in situ. Necesita reparación urgente."


@pytest.mark.asyncio
async def test_multiple_tickets_with_different_categories(async_client, admin_token):
    """Crear múltiples tickets con diferentes categorías."""

    categories = ["movilidad", "limpieza", "alumbrado_publico", "parques_y_jardines", "mobiliario_urbano"]

    created_ids = []

    for category in categories:
        payload = {
            "nombre": "María",
            "apellidos": "López",
            "nif": "87654321B",
            "telefono": "+34 777888999",
            "email": f"maria-{category}@example.com",
            "categoria": category,
            "description": f"Problema en {category}",
            "direccion_persona": "Calle del Ensayo 1",
            "ubicacion_incidencia": f"Zona de {category}",
        }

        resp = await async_client.post("/api/v1/tickets", json=payload)
        assert resp.status_code == 201
        created_ids.append(resp.json()["id"])

    # Verificar que todos los tickets se crearon
    list_resp = await async_client.get(
        "/api/v1/admin/tickets",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert list_resp.status_code == 200
    tickets = list_resp.json()
    assert len(tickets) >= len(categories)
    for ticket_id in created_ids:
        assert any(t["id"] == ticket_id for t in tickets)


@pytest.mark.asyncio
async def test_admin_stats_reflect_created_tickets(async_client, admin_token):
    """Las estadísticas del admin deben reflejar los tickets creados."""

    # Obtener stats iniciales
    initial_stats = await async_client.get(
        "/api/v1/admin/stats",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert initial_stats.status_code == 200
    initial_total = initial_stats.json()["total"]

    # Crear un nuevo ticket
    payload = {
        "nombre": "Carlos",
        "apellidos": "Martínez",
        "nif": "11111111C",
        "telefono": "+34 888999000",
        "email": "carlos@example.com",
        "categoria": "limpieza",
        "description": "Nueva incidencia de limpieza",
        "direccion_persona": "Calle Nueva 5",
        "ubicacion_incidencia": "Parque Central",
    }
    create_resp = await async_client.post("/api/v1/tickets", json=payload)
    assert create_resp.status_code == 201

    # Obtener stats nuevas
    new_stats = await async_client.get(
        "/api/v1/admin/stats",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert new_stats.status_code == 200
    new_total = new_stats.json()["total"]

    # Verificar que el total aumentó
    assert new_total == initial_total + 1


@pytest.mark.asyncio
async def test_ticket_spec_endpoint_provides_contract(async_client):
    """El endpoint de especificación debe proporcionar el contrato completo."""

    response = await async_client.get("/api/v1/tickets/spec")
    assert response.status_code == 200
    spec = response.json()

    # Verificar estructura del contrato
    assert "input_fields" in spec
    assert "persisted_fields" in spec
    assert "anonymized_fields" in spec
    assert "urgency_scale" in spec
    assert "categories" in spec
    assert "statuses" in spec

    # Verificar campos de entrada
    assert "nombre" in spec["input_fields"]
    assert "email" in spec["input_fields"]
    assert "categoria" in spec["input_fields"]

    # Verificar campos anonimizados
    assert "nombre" in spec["anonymized_fields"]
    assert "email" in spec["anonymized_fields"]
    assert "nif" in spec["anonymized_fields"]

    # Verificar escalas
    assert spec["urgency_scale"] == [1, 2, 3, 4, 5]
    assert "limpieza" in spec["categories"]
    assert "movilidad" in spec["categories"]
    assert "pending_review" in spec["statuses"]
    assert "resolved" in spec["statuses"]


# ---------------------------------------------------------------------------
# Protección de endpoints
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_admin_endpoints_require_authentication(async_client):
    """Los endpoints de admin deben requerir autenticación."""

    # Intentar acceder sin token
    response = await async_client.get("/api/v1/admin/dashboard")
    assert response.status_code == 401

    response = await async_client.get("/api/v1/admin/tickets")
    assert response.status_code == 401

    response = await async_client.get("/api/v1/admin/stats")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_invalid_token_is_rejected(async_client):
    """Los tokens inválidos deben ser rechazados."""

    response = await async_client.get(
        "/api/v1/admin/dashboard",
        headers={"Authorization": "Bearer invalid-token"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_ticket_creation_with_invalid_nif(async_client):
    """La creación de ticket con NIF inválido debe fallar."""

    payload = {
        "nombre": "Test",
        "apellidos": "User",
        "nif": "INVALID",  # NIF inválido
        "telefono": "+34 666777888",
        "email": "test@example.com",
        "categoria": "limpieza",
        "description": "Test",
        "direccion_persona": "Test",
        "ubicacion_incidencia": "Test",
    }

    response = await async_client.post("/api/v1/tickets", json=payload)
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_ticket_creation_with_invalid_email(async_client):
    """La creación de ticket con email inválido debe fallar."""

    payload = {
        "nombre": "Test",
        "apellidos": "User",
        "nif": "12345678A",
        "telefono": "+34 666777888",
        "email": "not-an-email",  # Email inválido
        "categoria": "limpieza",
        "description": "Test",
        "direccion_persona": "Test",
        "ubicacion_incidencia": "Test",
    }

    response = await async_client.post("/api/v1/tickets", json=payload)
    assert response.status_code == 422  # Validation error
