"""Tests de integración del servicio de tickets.

Propósito: verificar el flujo completo de creación, consulta y revisión
de tickets usando una BD SQLite en memoria.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.tickets import (
    TicketAdminDecision,
    TicketCategory,
    TicketCreateInput,
    TicketStatus,
)
from src.services import ticket_service
from src.services.ticket_service import MLServiceUnavailable


@pytest.fixture(autouse=True)
def mock_ml_success(monkeypatch):
    async def _fake_predict(*_args, **_kwargs):
        class FakeResult:
            urgency = 3
            category = TicketCategory.limpieza

        return FakeResult()

    monkeypatch.setattr("src.services.ticket_service.call_ml_predict", _fake_predict)


@pytest.fixture
def sample_input() -> TicketCreateInput:
    return TicketCreateInput(
        nombre="Pedro",
        apellidos="Martínez Gil",
        nif="87654321B",
        telefono="+34 611222333",
        email="pedro@example.com",
        categoria=TicketCategory.limpieza,
        description="Contenedores de basura llenos hace tres días en la plaza.",
        direccion_persona="Avenida de la Paz 10",
        ubicacion_incidencia="Plaza del Mercado",
    )


@pytest.mark.asyncio
async def test_create_ticket_persists_in_db(db_session: AsyncSession, sample_input):
    """El ticket debe guardarse en BD y devolver un registro con ID asignado."""

    record = await ticket_service.create_ticket(db_session, sample_input)

    assert record.id is not None
    assert record.id > 0
    assert record.categoria == TicketCategory.limpieza
    assert record.description == sample_input.description


@pytest.mark.asyncio
async def test_create_ticket_fails_when_ml_unavailable(
    db_session: AsyncSession, sample_input, monkeypatch
):
    """Sin servicio ML disponible, se debe bloquear la creación del ticket."""

    async def _fake_none(*_args, **_kwargs):
        return None

    monkeypatch.setattr("src.services.ticket_service.call_ml_predict", _fake_none)

    with pytest.raises(MLServiceUnavailable):
        await ticket_service.create_ticket(db_session, sample_input)


@pytest.mark.asyncio
async def test_get_ticket_returns_existing(db_session: AsyncSession, sample_input):
    """get_ticket debe devolver el registro correcto por ID."""

    created = await ticket_service.create_ticket(db_session, sample_input)
    fetched = await ticket_service.get_ticket(db_session, created.id)

    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.description == created.description


@pytest.mark.asyncio
async def test_get_ticket_returns_none_for_missing(db_session: AsyncSession):
    """get_ticket debe devolver None si el ticket no existe."""

    result = await ticket_service.get_ticket(db_session, ticket_id=99999)

    assert result is None


@pytest.mark.asyncio
async def test_list_tickets_returns_created(db_session: AsyncSession, sample_input):
    """list_tickets debe incluir los tickets recién creados."""

    await ticket_service.create_ticket(db_session, sample_input)
    tickets = await ticket_service.list_tickets(db_session)

    assert len(tickets) >= 1
    assert any(t.category == TicketCategory.limpieza for t in tickets)


@pytest.mark.asyncio
async def test_admin_review_sets_final_fields(db_session: AsyncSession, sample_input):
    """La revisión del admin debe actualizar urgencia, categoría, estado y reviewer."""

    created = await ticket_service.create_ticket(db_session, sample_input)

    decision = TicketAdminDecision(
        status=TicketStatus.in_progress,
        notes="Revisado manualmente por admin.",
    )
    reviewed = await ticket_service.admin_review_ticket(
        db_session, created.id, decision, reviewer_username="api_user"
    )

    assert reviewed is not None
    # La predicción de la IA se mantiene intacta tras la revisión
    assert reviewed.prediccion_urgencia is not None
    assert reviewed.prediccion_categoria is not None
    assert reviewed.status == TicketStatus.in_progress
    assert reviewed.reviewed_by == "api_user"
    assert reviewed.reviewed_at is not None


@pytest.mark.asyncio
async def test_admin_review_missing_ticket_returns_none(db_session: AsyncSession):
    """La revisión sobre un ticket inexistente debe devolver None."""

    decision = TicketAdminDecision(
        status=TicketStatus.accepted,
    )
    result = await ticket_service.admin_review_ticket(
        db_session, ticket_id=99999, decision=decision, reviewer_username="api_user"
    )

    assert result is None


@pytest.mark.asyncio
async def test_dashboard_stats_counts_correctly(db_session: AsyncSession, sample_input):
    """Las estadísticas deben reflejar el número de tickets creados."""

    await ticket_service.create_ticket(db_session, sample_input)
    await ticket_service.create_ticket(db_session, sample_input)

    stats = await ticket_service.get_dashboard_stats(db_session)

    assert stats.total >= 2
