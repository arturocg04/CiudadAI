"""Modelo de Incidencias/Reportes ciudadanos.

Propósito: definir la estructura de datos para incidencias ciudadanas con validación.
"""

from datetime import datetime

from pydantic import BaseModel, Field, validator


class IncidentBase(BaseModel):
    """Datos base de una incidencia."""

    nombre: str = Field(..., min_length=1, example="Elena")
    apellidos: str = Field(..., min_length=1, example="Pérez Garrido")
    nif: str = Field(..., min_length=9, max_length=9, example="66608986C")
    telefono: str = Field(..., min_length=9, max_length=9, example="656964241")
    email: str = Field(..., example="elenaperez847@example.com")
    categoria: str = Field(..., example="Movilidad")
    description: str = Field(..., min_length=10, example="En la Avenida de...")
    canal: str = Field(default="App", example="App")
    direccion_persona: str = Field(..., example="Calle Obispo Hu...")
    ubicacion_incid: str = Field(..., example="37.185, -3.596 - Junto a...")
    lid: int | None = Field(None, example=1001)
    urgencia: int | None = Field(None, ge=1, le=5, example=4)
    fecha: datetime = Field(default_factory=datetime.utcnow)
    estado: str = Field(default="nuevo", example="nuevo")

    @validator("nif")
    def validate_nif(cls, v):
        if not v.isalnum():
            raise ValueError("NIF debe ser alfanumérico")
        return v.upper()

    @validator("telefono")
    def validate_telefono(cls, v):
        if not v.isdigit():
            raise ValueError("Teléfono debe contener solo dígitos")
        return v

    @validator("estado")
    def validate_estado(cls, v):
        valid_states = ["nuevo", "pendiente", "cerrado"]
        if v not in valid_states:
            raise ValueError(f"Estado debe ser uno de: {valid_states}")
        return v


class IncidentCreate(IncidentBase):
    """Input para crear una incidencia (sin urgencia ni fecha)."""

    pass


class IncidentResponse(IncidentBase):
    """Response al crear una incidencia."""

    id: int = Field(..., example=1001)
    urgencia: int = Field(..., ge=1, le=5, example=4)
    fecha: datetime = Field(...)
    estado: str = Field(default="nuevo", example="nuevo")

    class Config:
        from_attributes = True


class IncidentDetail(IncidentResponse):
    """Detalle completo de una incidencia para el panel del trabajador."""

    pass


class IncidentUpdate(BaseModel):
    """Input para actualizar estado de una incidencia."""

    estado: str = Field(..., example="pendiente")

    @validator("estado")
    def validate_estado(cls, v):
        valid_states = ["nuevo", "pendiente", "cerrado"]
        if v not in valid_states:
            raise ValueError(f"Estado debe ser uno de: {valid_states}")
        return v
