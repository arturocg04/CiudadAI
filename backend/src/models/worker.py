"""Modelo de Trabajadores.

Propósito: definir la estructura de datos para trabajadores/personal de la plataforma.
"""


from pydantic import BaseModel, EmailStr, Field


class WorkerBase(BaseModel):
    """Datos base de un trabajador."""

    email: EmailStr = Field(..., example="worker@ciudadai.com")
    nombre: str = Field(..., min_length=1, example="Juan")
    apellidos: str = Field(..., min_length=1, example="García López")
    telefono: str = Field(default="", example="666777888")


class WorkerCreate(WorkerBase):
    """Input para crear un trabajador con contraseña."""

    password: str = Field(..., min_length=8, example="SecurePass123")


class WorkerResponse(WorkerBase):
    """Response al crear/recuperar un trabajador."""

    id: int = Field(..., example=1)
    active: bool = Field(default=True)

    class Config:
        from_attributes = True


class WorkerLogin(BaseModel):
    """Input para login de trabajador."""

    email: EmailStr = Field(..., example="worker@ciudadai.com")
    password: str = Field(..., example="SecurePass123")
