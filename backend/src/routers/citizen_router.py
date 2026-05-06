"""Router de ciudadanos.

Propósito: exponer rutas públicas para ciudadanos: creación de incidencias
y consulta de estado por ID. No requiere autenticación[cite: 1].
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.common.responses import COMMON_ERROR_RESPONSES
from src.constants import API_TAGS
from src.db.session import get_db
from src.deps import get_current_registered_user_dep
from src.models.auth import CurrentUser
from src.models.tickets import (
    TicketAnonymizedRecord,
    TicketCreateInputForUser,
    TicketStatus,
    TicketSummary,
)
from src.services import ticket_service
from src.services.ticket_service import MLServiceUnavailable

citizen_router = APIRouter(prefix="/citizen", tags=[API_TAGS["citizen"]])


@citizen_router.post(
    "/tickets",
    status_code=status.HTTP_201_CREATED,
    responses=COMMON_ERROR_RESPONSES,
    summary="Crear nueva incidencia",
)
async def citizen_create_ticket(
    body: TicketCreateInputForUser,
    user: CurrentUser = Depends(get_current_registered_user_dep),
    db: AsyncSession = Depends(get_db),
) -> TicketAnonymizedRecord:
    """
    El ciudadano reporta una nueva incidencia.
    Los datos se anonimizan y la IA predice la urgencia automáticamente.
    """

    try:
        return await ticket_service.create_ticket_for_user(db, body, user)
    except MLServiceUnavailable as err:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No se pudo clasificar la incidencia en este momento. Inténtalo más tarde.",
        ) from err


@citizen_router.get(
    "/my-tickets",
    status_code=status.HTTP_200_OK,
    responses=COMMON_ERROR_RESPONSES,
    summary="Lista de tickets del usuario",
)
async def citizen_list_my_tickets(
    user: CurrentUser = Depends(get_current_registered_user_dep),
    db: AsyncSession = Depends(get_db),
) -> list[TicketSummary]:
    """Devuelve los tickets del usuario actual."""

    return await ticket_service.get_tickets_for_user(db, user.id)


@citizen_router.delete(
    "/tickets/{ticket_id}",
    status_code=status.HTTP_200_OK,
    responses=COMMON_ERROR_RESPONSES,
    summary="Eliminar un ticket propio",
)
async def citizen_delete_ticket(
    ticket_id: int,
    user: CurrentUser = Depends(get_current_registered_user_dep),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Permite al usuario eliminar uno de sus propios tickets."""

    deleted = await ticket_service.delete_ticket_for_user(db, ticket_id, user.id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket #{ticket_id} no encontrado.",
        )
    return {"message": "Ticket eliminado."}


@citizen_router.get(
    "/dashboard",
    status_code=status.HTTP_200_OK,
    responses=COMMON_ERROR_RESPONSES,
    summary="Dashboard del ciudadano",
)
async def citizen_dashboard() -> dict:
    """Devuelve información de bienvenida para el panel del ciudadano."""

    return {
        "message": "Bienvenido al panel ciudadano.",
        "content": {
            "title": "Reporta y sigue tus incidencias",
            "description": (
                "Aquí puedes gestionar tus solicitudes y ver el estado de tu ciudad "
                "de manera sencilla."
            ),
        },
    }


@citizen_router.get(
    "/tickets/{ticket_id}/status",
    status_code=status.HTTP_200_OK,
    responses=COMMON_ERROR_RESPONSES,
    summary="Consultar estado de un ticket por ID",
)
async def get_ticket_status(
    ticket_id: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Permite consultar si una incidencia está 'pendiente' o 'cerrada'
    introduciendo únicamente el ID del ticket[cite: 1].
    """

    record = await ticket_service.get_ticket(db, ticket_id)

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se ha encontrado ninguna incidencia con el ID #{ticket_id}.",
        )

    # Mapeo de estados según requerimientos: Resolved -> cerrado, resto -> pendiente[cite: 1, 20]
    estado_ciudadano = "cerrado" if record.status == "resolved" else "pendiente"

    return {
        "id": record.id,
        "estado": estado_ciudadano,
        "categoria": record.categoria,
        "fecha_creacion": record.fecha,
        "description": record.description,
        "ubicacion_incidencia": record.ubicacion_incidencia,
    }


@citizen_router.get(
    "/tickets",
    status_code=status.HTTP_200_OK,
    responses=COMMON_ERROR_RESPONSES,
    summary="Listar incidencias (Público)",
)
async def citizen_list_tickets(
    status_filter: TicketStatus | None = Query(default=None, alias="status"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> list[TicketSummary]:
    """
    Lista las incidencias del sistema de forma abierta.
    """

    return await ticket_service.list_tickets(db, status_filter, skip, limit)
