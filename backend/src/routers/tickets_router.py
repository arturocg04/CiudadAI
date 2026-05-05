"""Router del dominio de tickets.

Propósito: exponer los endpoints CRUD de incidencias para ciudadanos y admins.
Los endpoints de creación requieren rol citizen; los de revisión, rol admin.
La lógica de negocio se delega completamente a ticket_service.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.responses import COMMON_ERROR_RESPONSES
from src.constants import API_TAGS
from src.db.session import get_db
from src.deps import require_admin
from src.models.auth import CurrentUser
from src.models.tickets import (
    TicketAdminDecision,
    TicketAnonymizedRecord,
    TicketCategory,
    TicketContractSpec,
    TicketCreateInput,
    TicketStatus,
    TicketSummary,
)
from src.services import ticket_service
from src.services.ticket_service import MLServiceUnavailable

tickets_router = APIRouter(prefix="/tickets", tags=[API_TAGS["tickets"]])


# ---------------------------------------------------------------------------
# Endpoint de especificación del contrato (sin autenticación)
# ---------------------------------------------------------------------------


@tickets_router.get(
    "/spec",
    status_code=status.HTTP_200_OK,
    responses=COMMON_ERROR_RESPONSES,
    summary="Contrato del dominio de tickets",
)
async def ticket_spec() -> TicketContractSpec:
    """Devuelve el contrato base del dominio de tickets (sin autenticación)."""

    return TicketContractSpec(
        input_fields=[
            "nombre",
            "apellidos",
            "nif",
            "telefono",
            "email",
            "categoria",
            "description",
            "direccion_persona",
            "ubicacion_incidencia",
            "fecha",
        ],
        persisted_fields=[
            "id",
            "nombre",
            "apellidos",
            "nif",
            "telefono",
            "email",
            "categoria",
            "description",
            "urgencia",
            "fecha",
            "direccion_persona",
            "ubicacion_incidencia",
            "prediccion_urgencia",
            "prediccion_categoria",
            "status",
            "reviewed_by",
            "reviewed_at",
        ],
        anonymized_fields=["nombre", "apellidos", "nif", "telefono", "email"],
        urgency_scale=[1, 2, 3, 4, 5],
        categories=list(TicketCategory),
        statuses=list(TicketStatus),
    )


# ---------------------------------------------------------------------------
# Ciudadano: crear un ticket
# ---------------------------------------------------------------------------


@tickets_router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    responses=COMMON_ERROR_RESPONSES,
    summary="Crear nueva incidencia (ciudadano)",
)
async def create_ticket(
    body: TicketCreateInput, db: AsyncSession = Depends(get_db)
) -> TicketAnonymizedRecord:
    """Crea una nueva incidencia.

    El ciudadano envía sus datos personales; el backend los anonimiza antes de
    persistirlos y llama al servicio ML para predecir urgencia y categoría.
    """

    try:
        return await ticket_service.create_ticket(db, body)
    except MLServiceUnavailable:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No se pudo clasificar la incidencia en este momento. Inténtalo más tarde.",
        )


# ---------------------------------------------------------------------------
# Listar tickets (admin ve todos; ciudadano podría ver los suyos — aquí admin)
# ---------------------------------------------------------------------------


@tickets_router.get(
    "",
    status_code=status.HTTP_200_OK,
    responses=COMMON_ERROR_RESPONSES,
    summary="Listar tickets (admin)",
)
async def list_tickets(
    status_filter: TicketStatus | None = Query(default=None, alias="status"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _user: CurrentUser = Depends(require_admin),
) -> list[TicketSummary]:
    """Lista todos los tickets con paginación y filtro opcional de estado."""

    return await ticket_service.list_tickets(db, status_filter, skip, limit)


# ---------------------------------------------------------------------------
# Detalle de un ticket (admin)
# ---------------------------------------------------------------------------


@tickets_router.get(
    "/{ticket_id}",
    status_code=status.HTTP_200_OK,
    responses=COMMON_ERROR_RESPONSES,
    summary="Detalle de un ticket (admin)",
)
async def get_ticket(
    ticket_id: int,
    db: AsyncSession = Depends(get_db),
    _user: CurrentUser = Depends(require_admin),
) -> TicketAnonymizedRecord:
    """Devuelve el detalle completo de un ticket por ID."""

    record = await ticket_service.get_ticket(db, ticket_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket #{ticket_id} no encontrado.",
        )
    return record


# ---------------------------------------------------------------------------
# Admin: revisar un ticket
# ---------------------------------------------------------------------------


@tickets_router.patch(
    "/{ticket_id}/review",
    status_code=status.HTTP_200_OK,
    responses=COMMON_ERROR_RESPONSES,
    summary="Revisar y clasificar un ticket (admin)",
)
async def review_ticket(
    ticket_id: int,
    body: TicketAdminDecision,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_admin),
) -> TicketAnonymizedRecord:
    """El admin acepta o modifica la predicción del modelo y cierra la revisión."""

    record = await ticket_service.admin_review_ticket(
        db, ticket_id, body, user.username
    )
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket #{ticket_id} no encontrado.",
        )
    return record
