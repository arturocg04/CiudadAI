"""Contratos de dominio para incidencias y tickets.

Propósito: definir la base lógica de tickets, el payload del ciudadano, la
versión anonimizada que se persiste y los metadatos de revisión.
"""

import re
import unicodedata
from datetime import UTC, datetime
from enum import IntEnum, StrEnum

from pydantic import BaseModel, EmailStr, Field, validator


def _normalize_category(value: str) -> str:
    normalized = value.strip().lower()
    normalized = unicodedata.normalize("NFKD", normalized)
    normalized = "".join(
        character for character in normalized if not unicodedata.combining(character)
    )
    normalized = normalized.replace("-", "_").replace(" ", "_")
    normalized = re.sub(r"_+", "_", normalized)
    return normalized


class TicketCategory(StrEnum):
    """Taxonomía base para clasificar incidencias urbanas."""

    movilidad = "movilidad"
    limpieza = "limpieza"
    alumbrado_publico = "alumbrado_publico"
    parques_y_jardines = "parques_y_jardines"
    mobiliario_urbano = "mobiliario_urbano"
    otros = "otros"

    @classmethod
    def _missing_(cls, value: object):
        if not isinstance(value, str):
            return None

        normalized = _normalize_category(value)

        # Acepta el nombre del miembro (p.ej. "alumbrado_publico"),
        # el valor canónico (p.ej. "parques_y_jardines") y variantes
        # con espacios/acentos (p.ej. "Parques y jardines").
        for member in cls:
            if normalized == member.name or normalized == member.value:
                return member

        return None


class TicketUrgency(IntEnum):
    """Escala de urgencia usada por el modelo y la revisión manual."""

    minimum = 1
    low = 2
    medium = 3
    high = 4
    maximum = 5


class TicketStatus(StrEnum):
    """Estado operativo de un ticket."""

    pending_classification = "pending_classification"
    pending_review = "pending_review"
    accepted = "accepted"
    in_progress = "in_progress"
    resolved = "resolved"


class TicketCreateInput(BaseModel):
    """Payload que envía el ciudadano antes de anonimizar y persistir."""

    nombre: str = Field(min_length=1, max_length=120)
    apellidos: str = Field(min_length=1, max_length=180)
    nif: str = Field(min_length=9, max_length=9)
    telefono: str = Field(min_length=8, max_length=24)
    email: EmailStr = Field(min_length=5, max_length=254)
    categoria: TicketCategory
    description: str = Field(min_length=1, max_length=300)
    direccion_persona: str = Field(min_length=1, max_length=255)
    ubicacion_incidencia: str = Field(min_length=1, max_length=255)
    fecha: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @validator("nombre", "apellidos")
    def validate_name(cls, value: str) -> str:
        normalized = value.strip()
        if not re.fullmatch(r"[A-Za-zÁÉÍÓÚáéíóúÑñÜü\s]+", normalized):
            raise ValueError(
                "Solo se permiten letras y espacios en nombre y apellidos."
            )
        return normalized

    @validator("nif")
    def validate_nif_nie(cls, value: str) -> str:
        normalized = value.strip().upper()
        if not re.fullmatch(r"(?:\d{8}[A-Z]|[XYZ]\d{7}[A-Z])", normalized):
            raise ValueError("NIF/NIE debe tener formato válido.")
        return normalized


class TicketCreateInputForUser(BaseModel):
    """Payload simplificado para usuarios registrados."""

    categoria: TicketCategory
    description: str = Field(min_length=1, max_length=300)
    ubicacion_incidencia: str = Field(min_length=1, max_length=255)


class TicketAnonymizedRecord(BaseModel):
    """Versión que se persiste en BD con los nuevos campos de IA."""

    id: int | None = None
    nombre: str
    apellidos: str
    nif: str
    telefono: str
    email: str
    anon_fingerprint: str | None = None
    categoria: TicketCategory
    description: str
    fecha: datetime
    direccion_persona: str
    ubicacion_incidencia: str
    prediccion_urgencia: TicketUrgency | None = None
    prediccion_categoria: TicketCategory | None = None
    status: TicketStatus = TicketStatus.pending_classification
    reviewed_by: str | None = None
    reviewed_at: datetime | None = None
    admin_notes: str | None = None


class TicketClassificationResult(BaseModel):
    """Salida del servicio de inferencia para urgencia y categoría."""

    urgency: TicketUrgency = Field(description="Urgencia predicha por el modelo")
    category: TicketCategory = Field(description="Categoría predicha por el modelo")
    model_name: str = Field(min_length=1, max_length=120)
    model_version: str = Field(min_length=1, max_length=60)
    scored_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class TicketAdminDecision(BaseModel):
    """Acción del empleado sobre un ticket.

    El empleado puede ajustar la urgencia y cambiar el estado,
    además de introducir notas de resolución.
    """

    status: TicketStatus = TicketStatus.accepted
    prediccion_urgencia: TicketUrgency
    notes: str | None = Field(default=None, max_length=2000)


class TicketSummary(BaseModel):
    """Resumen mínimo del ticket para listados y dashboards."""

    id: int
    category: TicketCategory
    prediccion_urgencia: TicketUrgency | None = None
    prediccion_categoria: TicketCategory | None = None
    status: TicketStatus
    fecha: datetime
    ubicacion_incidencia: str
    description: str
    admin_notes: str | None = None


class TicketCitizenView(BaseModel):
    """Vista del ticket para ciudadanos que incluye notas del admin."""

    id: int
    category: TicketCategory
    prediccion_urgencia: TicketUrgency | None = None
    prediccion_categoria: TicketCategory | None = None
    status: TicketStatus
    fecha: datetime
    ubicacion_incidencia: str
    description: str
    admin_notes: str | None = None
    reviewed_by: str | None = None
    reviewed_at: datetime | None = None


class TicketDashboardStats(BaseModel):
    """Estadísticas agregadas para el dashboard del admin."""

    total: int = 0
    new_tickets: int = 0
    pending_review: int = 0
    open: int = 0
    resolved: int = 0
    # Tickets donde la categoría del ciudadano difiere de la predicción del modelo.
    # El empleado debe revisarlos con atención.
    category_mismatch: int = 0
    by_urgency: dict[TicketUrgency, int] = Field(default_factory=dict)
    by_category: dict[TicketCategory, int] = Field(default_factory=dict)


class TicketContractSpec(BaseModel):
    """Contrato resumido para documentar la base del dominio de tickets."""

    input_fields: list[str]
    persisted_fields: list[str]
    anonymized_fields: list[str]
    urgency_scale: list[int]
    categories: list[TicketCategory]
    statuses: list[TicketStatus]
