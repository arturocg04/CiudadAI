import hashlib
import hmac
import logging
import re

from src.config import settings
from src.models.tickets import TicketCreateInput

logger = logging.getLogger(__name__)


def anonymize_ticket(ticket_input: TicketCreateInput) -> dict:
    letra_inicial = ticket_input.nombre[0] if ticket_input.nombre else "*"
    logger.info("Procesando anonimización para: %s***", letra_inicial)
    pseudonym = build_pseudonym(ticket_input)
    return {
        "nombre": anonimizar_valor(ticket_input.nombre, "nombre"),
        "apellidos": anonimizar_valor(ticket_input.apellidos, "apellidos"),
        "nif": anonimizar_valor(ticket_input.nif, "nif"),
        "telefono": anonimizar_valor(ticket_input.telefono, "telefono"),
        "email": anonimizar_valor(ticket_input.email, "email"),
        "anon_fingerprint": pseudonym,
        "categoria": ticket_input.categoria,
        "description": limpiar_descripcion(ticket_input.description, ticket_input),
        "direccion_persona": ticket_input.direccion_persona,
        "ubicacion_incidencia": ticket_input.ubicacion_incidencia,
        "fecha": ticket_input.fecha,
    }


def anonimizar_valor(texto: str, tipo: str) -> str:
    if not texto:
        return ""
    texto = str(texto).strip()
    if not texto:
        return ""

    if tipo in ["nombre", "apellidos"]:
        return f"{texto[0]}***"
    if tipo == "nif":
        return "[NIF_OCULTO]"
    if tipo == "telefono":
        return f"{texto[0]}***"
    if tipo == "email":
        try:
            usuario, dominio_completo = texto.split("@")
            partes_dominio = dominio_completo.rsplit(".", 1)
            tld = partes_dominio[1] if len(partes_dominio) == 2 else ""
            return f"{usuario[0]}***@***.{tld}" if tld else f"{usuario[0]}***@***"
        except ValueError:
            return "[EMAIL_OCULTO]"
    return texto


def limpiar_descripcion(descripcion: str, ticket: TicketCreateInput) -> str:
    if not descripcion:
        return ""
    texto_limpio = descripcion
    if ticket.nif:
        texto_limpio = re.sub(
            re.escape(ticket.nif),
            "[NIF_OCULTO]",
            texto_limpio,
            flags=re.IGNORECASE,
        )
    if ticket.email:
        texto_limpio = re.sub(
            re.escape(ticket.email),
            anonimizar_valor(ticket.email, "email"),
            texto_limpio,
            flags=re.IGNORECASE,
        )
    if ticket.telefono:
        texto_limpio = re.sub(
            re.escape(ticket.telefono),
            anonimizar_valor(ticket.telefono, "telefono"),
            texto_limpio,
            flags=re.IGNORECASE,
        )
    if ticket.nombre and len(ticket.nombre) > 2:
        texto_limpio = re.sub(
            r"\b" + re.escape(ticket.nombre) + r"\b",
            anonimizar_valor(ticket.nombre, "nombre"),
            texto_limpio,
            flags=re.IGNORECASE,
        )
    if ticket.apellidos and len(ticket.apellidos) > 2:
        texto_limpio = re.sub(
            r"\b" + re.escape(ticket.apellidos) + r"\b",
            anonimizar_valor(ticket.apellidos, "apellidos"),
            texto_limpio,
            flags=re.IGNORECASE,
        )

    texto_limpio = re.sub(r"\b\d{8,9}\s*[A-Za-z]?\b", "[NRO_OCULTO]", texto_limpio)
    texto_limpio = re.sub(
        r"[\w\.-]+@[\w\.-]+\.\w+",
        lambda m: anonimizar_valor(m.group(0), "email"),
        texto_limpio,
    )
    return texto_limpio


def build_pseudonym(ticket_input: TicketCreateInput) -> str:
    partes = [
        _normalize_token(ticket_input.nombre),
        _normalize_token(ticket_input.nif),
        _normalize_token(ticket_input.email),
        _normalize_token(ticket_input.telefono),
    ]
    payload = "|".join(part for part in partes if part)
    secret = settings.anonymizer_secret
    if not secret:
        return ""
    digest = hmac.new(
        secret.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return digest[:32]


def _normalize_token(value: str | None) -> str:
    if not value:
        return ""
    return str(value).strip().lower()
