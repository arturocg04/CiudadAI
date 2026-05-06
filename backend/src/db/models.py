from datetime import UTC, datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Clase base de la que heredan todos los modelos ORM."""


class UserORM(Base):
    """Tabla de usuarios registrados."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(120))
    apellidos: Mapped[str] = mapped_column(String(180))
    nif: Mapped[str] = mapped_column(String(32), unique=True)
    telefono: Mapped[str] = mapped_column(String(24), unique=True)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    domicilio: Mapped[str] = mapped_column(String(255))
    password_hash: Mapped[str] = mapped_column(String(128))
    role: Mapped[str] = mapped_column(
        String(20), default="citizen"
    )  # "citizen" or "admin"
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )


class TicketORM(Base):
    """Tabla principal de tickets anonimizados.

    Los campos personales almacenados aquí ya han pasado por la capa
    de anonimización: nunca contienen datos crudos del ciudadano.
    """

    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # --- Referencia al usuario ---
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # --- Datos anonimizados del ciudadano ---
    nombre: Mapped[str] = mapped_column(String(120))
    apellidos: Mapped[str] = mapped_column(String(180))
    nif: Mapped[str] = mapped_column(String(32))
    telefono: Mapped[str] = mapped_column(String(24))
    email: Mapped[str] = mapped_column(String(254))
    anon_fingerprint: Mapped[str | None] = mapped_column(String(128), nullable=True)

    # --- Datos de la incidencia ---
    categoria: Mapped[str] = mapped_column(String(60))
    description: Mapped[str] = mapped_column(Text)
    direccion_persona: Mapped[str] = mapped_column(String(255))
    ubicacion_incidencia: Mapped[str] = mapped_column(String(255))

    # --- Timestamps ---
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )

    # --- Control de IA ---
    prediccion_urgencia: Mapped[int | None] = mapped_column(Integer, nullable=True)
    prediccion_categoria: Mapped[str | None] = mapped_column(String(60), nullable=True)

    # --- Estado y revisión ---
    status: Mapped[str] = mapped_column(String(40), default="pending_classification")
    reviewed_by: Mapped[str | None] = mapped_column(String(120), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    admin_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
