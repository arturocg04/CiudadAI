"""Tests unitarios del stub de anonimización.

Propósito: verificar que el stub devuelve los campos correctos y que cuando
el compañero lo implemente, los campos sensibles quedan modificados.
"""

from datetime import datetime

import pytest

from src.models.tickets import TicketCategory, TicketCreateInput
from src.services.anonymizer import anonymize_ticket


@pytest.fixture
def sample_input() -> TicketCreateInput:
    return TicketCreateInput(
        nombre="Ana",
        apellidos="García López",
        nif="12345678A",
        telefono="+34 600123456",
        email="ana@example.com",
        categoria=TicketCategory.movilidad,
        description="Hay un bache enorme en la Calle Mayor.",
        direccion_persona="Calle Mayor 1",
        ubicacion_incidencia="Esquina con la Plaza Central",
    )


def test_anonymize_returns_dict(sample_input):
    """El stub debe devolver un diccionario con las claves del contrato."""

    result = anonymize_ticket(sample_input)

    assert isinstance(result, dict)
    expected_keys = {
        "nombre",
        "apellidos",
        "nif",
        "telefono",
        "email",
        "anon_fingerprint",
        "categoria",
        "description",
        "direccion_persona",
        "ubicacion_incidencia",
        "fecha",
    }
    assert expected_keys == set(result.keys())


def test_anonymize_preserves_non_sensitive_fields(sample_input):
    """Campos no sensibles deben llegar sin modificar al resultado."""

    result = anonymize_ticket(sample_input)

    assert result["categoria"] == TicketCategory.movilidad
    assert result["description"] == sample_input.description
    assert result["direccion_persona"] == sample_input.direccion_persona
    assert result["ubicacion_incidencia"] == sample_input.ubicacion_incidencia


def test_anonymize_fecha_is_datetime(sample_input):
    """El campo fecha debe ser un datetime con tzinfo."""

    result = anonymize_ticket(sample_input)

    assert isinstance(result["fecha"], datetime)
    assert result["fecha"].tzinfo is not None


def test_anonymize_masks_sensitive_fields(sample_input):
    result = anonymize_ticket(sample_input)

    assert result["nombre"] == "A***"
    assert result["apellidos"] == "G***"
    assert result["nif"] == "[NIF_OCULTO]"
    assert result["telefono"].endswith("***")
    assert "@***" in result["email"]
    assert result["anon_fingerprint"]


def test_anonymize_fingerprint_is_deterministic(sample_input):
    first = anonymize_ticket(sample_input)
    second = anonymize_ticket(sample_input)

    assert first["anon_fingerprint"] == second["anon_fingerprint"]


def test_anonymize_fingerprint_changes_with_name(sample_input):
    other = sample_input.model_copy(update={"nombre": "Bea"})

    first = anonymize_ticket(sample_input)
    second = anonymize_ticket(other)

    assert first["anon_fingerprint"] != second["anon_fingerprint"]
