"""Servicio de negocio para tickets de incidencias.

Propósito: orquestar el flujo completo de una incidencia:
  1. Anonimizar los datos personales (stub, pendiente del compañero).
  2. Llamar al servicio de ML para obtener predicción de urgencia y categoría.
  3. Persistir el ticket anonimizado en PostgreSQL.
  4. Exponer operaciones de lectura y revisión para admin y ciudadano.

Ninguna función de este módulo conoce detalles HTTP: recibe y devuelve
objetos de dominio definidos en src/models/tickets.py.
"""

import logging
from datetime import UTC, datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.clients.ml_client import call_ml_predict
from src.db.models import TicketORM
from src.models.auth import CurrentUser
from src.models.tickets import (
    TicketAdminDecision,
    TicketAnonymizedRecord,
    TicketCategory,
    TicketCreateInput,
    TicketCreateInputForUser,
    TicketDashboardStats,
    TicketStatus,
    TicketSummary,
    TicketUrgency,
)
from src.services.anonymizer import anonymize_ticket

logger = logging.getLogger(__name__)


class MLServiceUnavailable(Exception):
    """Señala que el servicio ML no respondió y se debe bloquear la creación."""


# ---------------------------------------------------------------------------
# Helpers de conversión ORM ↔ dominio
# ---------------------------------------------------------------------------


def _orm_to_record(row: TicketORM) -> TicketAnonymizedRecord:
    return TicketAnonymizedRecord(
        id=row.id,
        nombre=row.nombre,
        apellidos=row.apellidos,
        nif=row.nif,
        telefono=row.telefono,
        email=row.email,
        anon_fingerprint=row.anon_fingerprint,
        categoria=TicketCategory(row.categoria),
        description=row.description,
        fecha=row.fecha,
        direccion_persona=row.direccion_persona,
        ubicacion_incidencia=row.ubicacion_incidencia,
        # Mapeo a los nuevos atributos
        prediccion_urgencia=TicketUrgency(row.prediccion_urgencia)
        if row.prediccion_urgencia
        else None,
        prediccion_categoria=TicketCategory(row.prediccion_categoria)
        if row.prediccion_categoria
        else None,
        status=TicketStatus(row.status),
        reviewed_by=row.reviewed_by,
        reviewed_at=row.reviewed_at,
        admin_notes=row.admin_notes,
    )


def _orm_to_summary(row: TicketORM) -> TicketSummary:
    """Convierte una fila ORM al resumen mínimo para listados."""
    return TicketSummary(
        id=row.id,  # type: ignore[arg-type]
        category=TicketCategory(row.categoria),
        status=TicketStatus(row.status),
        fecha=row.fecha,
        ubicacion_incidencia=row.ubicacion_incidencia,
        description=row.description,
        prediccion_urgencia=TicketUrgency(row.prediccion_urgencia)
        if row.prediccion_urgencia
        else None,
        prediccion_categoria=TicketCategory(row.prediccion_categoria)
        if row.prediccion_categoria
        else None,
    )


# ---------------------------------------------------------------------------
# Operaciones principales
# ---------------------------------------------------------------------------


async def create_ticket(
    db: AsyncSession,
    ticket_input: TicketCreateInput,
) -> TicketAnonymizedRecord:
    """Crea un nuevo ticket siguiendo el flujo completo.

    Pasos:
      1. Anonimizar los datos personales del ciudadano (stub por ahora).
      2. Llamar al servicio ML para predecir urgencia y categoría.
      3. Persistir el ticket anonimizado con los metadatos de predicción.

    Si el servicio ML no responde, el ticket queda en `pending_classification`
    y podrá ser clasificado manualmente por el admin.
    """

    # Paso 1: anonimización (stub hasta que el compañero lo implemente)
    anon_data = anonymize_ticket(ticket_input)

    # Paso 2: inferencia ML (obligatoria)
    ml_result = await call_ml_predict(
        description=ticket_input.description,
        categoria=ticket_input.categoria,
    )

    if ml_result is None:
        logger.warning("Servicio ML no disponible; se bloquea la creación del ticket.")
        raise MLServiceUnavailable("ML service unavailable")

    # Paso 3: determinar estado y campos de predicción
    ticket_status = TicketStatus.pending_review
    prediccion_urgencia = int(ml_result.urgency)
    prediccion_categoria = str(ml_result.category)
    logger.info(
        "ML predijo urgencia=%s, categoria=%s para nuevo ticket.",
        ml_result.urgency,
        ml_result.category,
    )

    # Paso 4: persistir en BD
    ticket_orm = TicketORM(
        nombre=anon_data["nombre"],
        apellidos=anon_data["apellidos"],
        nif=anon_data["nif"],
        telefono=anon_data["telefono"],
        email=anon_data["email"],
        anon_fingerprint=anon_data.get("anon_fingerprint"),
        categoria=str(anon_data["categoria"]),
        description=anon_data["description"],
        direccion_persona=anon_data["direccion_persona"],
        ubicacion_incidencia=anon_data["ubicacion_incidencia"],
        fecha=anon_data["fecha"],
        prediccion_urgencia=prediccion_urgencia,
        prediccion_categoria=prediccion_categoria,
        status=str(ticket_status),
    )

    db.add(ticket_orm)
    await db.commit()
    await db.refresh(ticket_orm)

    logger.info("Ticket #%s creado con status=%s.", ticket_orm.id, ticket_status)
    return _orm_to_record(ticket_orm)


async def get_ticket(
    db: AsyncSession,
    ticket_id: int,
) -> TicketAnonymizedRecord | None:
    """Obtiene un ticket por su ID. Retorna None si no existe."""

    result = await db.execute(select(TicketORM).where(TicketORM.id == ticket_id))
    row = result.scalar_one_or_none()
    return _orm_to_record(row) if row else None


async def list_tickets(
    db: AsyncSession,
    status_filter: TicketStatus | None = None,
    skip: int = 0,
    limit: int = 50,
) -> list[TicketSummary]:
    """Lista tickets con paginación y filtro opcional de estado."""

    query = (
        select(TicketORM)
        .order_by(TicketORM.prediccion_urgencia.desc().nulls_last(), TicketORM.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    if status_filter is not None:
        query = query.where(TicketORM.status == str(status_filter))

    result = await db.execute(query)
    rows = result.scalars().all()
    return [_orm_to_summary(row) for row in rows]


async def admin_review_ticket(
    db: AsyncSession,
    ticket_id: int,
    decision: TicketAdminDecision,
    reviewer_username: str,
) -> TicketAnonymizedRecord | None:
    """Registra la respuesta del empleado y cierra la incidencia.

    El empleado puede ajustar la urgencia y cambiar el estado,
    además de añadir notas de resolución.
    """

    # 1. Verificar si el ticket existe
    result = await db.execute(select(TicketORM).where(TicketORM.id == ticket_id))
    row = result.scalar_one_or_none()
    if row is None:
        return None

    # 2. Actualizar solo los campos que existen tras el cambio de atributos
    await db.execute(
        update(TicketORM)
        .where(TicketORM.id == ticket_id)
        .values(
            status=str(decision.status),
            prediccion_urgencia=int(decision.prediccion_urgencia),
            reviewed_by=reviewer_username,
            reviewed_at=datetime.now(UTC),
            admin_notes=decision.notes,
        )
    )

    await db.commit()
    await db.refresh(row)

    logger.info(
        "Ticket #%s cerrado por empleado %s con estado %s.",
        ticket_id,
        reviewer_username,
        decision.status,
    )

    return _orm_to_record(row)


async def get_dashboard_stats(db: AsyncSession) -> TicketDashboardStats:
    """Calcula estadísticas agregadas para el dashboard del admin."""

    # Total de tickets
    total_result = await db.execute(select(func.count()).select_from(TicketORM))
    total = total_result.scalar_one()

    # Pendientes de revisión
    pending_result = await db.execute(
        select(func.count()).where(TicketORM.status == str(TicketStatus.pending_review))
    )
    pending_review = pending_result.scalar_one()

    # Resueltos
    resolved_result = await db.execute(
        select(func.count()).where(TicketORM.status == str(TicketStatus.resolved))
    )
    resolved = resolved_result.scalar_one()

    # Nuevos tickets que todavía no han sido abiertos para revisión.
    new_result = await db.execute(
        select(func.count()).where(
            TicketORM.status == str(TicketStatus.pending_classification)
        )
    )
    new_tickets = new_result.scalar_one()

    # Abiertos (todos los que no están resueltos)
    open_count = total - resolved

    # Tickets con discordancia entre la categoría del ciudadano y la del modelo.
    # Solo aplica cuando el modelo ha predicho (prediccion_categoria no es None).
    mismatch_result = await db.execute(
        select(func.count()).where(
            TicketORM.prediccion_categoria.isnot(None),
            TicketORM.categoria != TicketORM.prediccion_categoria,
        )
    )
    category_mismatch = mismatch_result.scalar_one()

    # Distribución por urgencia según el modelo (la única fuente de verdad de urgencia)
    urgency_result = await db.execute(
        select(TicketORM.prediccion_urgencia, func.count())
        .where(TicketORM.prediccion_urgencia.isnot(None))
        .group_by(TicketORM.prediccion_urgencia)
    )
    by_urgency: dict[TicketUrgency, int] = {
        TicketUrgency(u): c for u, c in urgency_result.all()
    }

    # Distribución por categoría del ciudadano
    category_result = await db.execute(
        select(TicketORM.categoria, func.count()).group_by(TicketORM.categoria)
    )
    by_category: dict[TicketCategory, int] = {
        TicketCategory(cat): c for cat, c in category_result.all()
    }

    return TicketDashboardStats(
        total=total,
        new_tickets=new_tickets,
        pending_review=pending_review,
        open=open_count,
        resolved=resolved,
        category_mismatch=category_mismatch,
        by_urgency=by_urgency,
        by_category=by_category,
    )


async def create_ticket_for_user(
    db: AsyncSession,
    ticket_input: TicketCreateInputForUser,
    user,
) -> TicketAnonymizedRecord:
    """Crea un nuevo ticket para un usuario registrado."""

    # Usar datos del usuario.
    # Para preservar privacidad y no requerir datos sensibles del usuario,
    # rellenamos campos opcionales con valores válidos si no están disponibles.
    from src.models.tickets import TicketCreateInput

    def _safe_nif(value: str | None) -> str:
        return value if value and len(value.strip()) >= 9 else "00000000A"

    def _safe_phone(value: str | None) -> str:
        return value if value and len(value.strip()) >= 8 else "600000000"

    def _safe_address(value: str | None) -> str:
        return value if value and len(value.strip()) >= 1 else "Dirección no disponible"

    full_input = TicketCreateInput(
        nombre=user.nombre or "Ciudadano",
        apellidos=user.apellidos or "Anónimo",
        nif=_safe_nif(getattr(user, "nif", None)),
        telefono=_safe_phone(getattr(user, "telefono", None)),
        email=user.email,
        categoria=ticket_input.categoria,
        description=ticket_input.description,
        direccion_persona=_safe_address(getattr(user, "domicilio", None)),
        ubicacion_incidencia=ticket_input.ubicacion_incidencia,
    )

    # Crear ticket normal pero con user_id
    record = await create_ticket(db, full_input)
    # Actualizar user_id en el ORM
    await db.execute(
        update(TicketORM).where(TicketORM.id == record.id).values(user_id=user.id)
    )
    await db.commit()
    return record


async def get_tickets_for_user(
    db: AsyncSession,
    user_id: int,
) -> list[TicketSummary]:
    """Obtiene los tickets de un usuario."""

    query = select(TicketORM).where(TicketORM.user_id == user_id)
    result = await db.execute(query)
    rows = result.scalars().all()
    return [_orm_to_summary(row) for row in rows]
