"""Fixtures compartidas para pruebas.

Propósito: crear un cliente de pruebas reutilizable y una BD en memoria
para tests de integración sin necesitar PostgreSQL real.
"""

import os

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.app import app
from src.config import settings
from src.db.models import Base
from src.db.session import get_db
from src.models.tickets import TicketCategory, TicketClassificationResult, TicketUrgency
from src.services import ticket_service
from src.services.auth_service import (
    USERS_DB,
    _build_users_db_from_settings,
    create_access_token,
)

# ---------------------------------------------------------------------------
# Mock auth setup
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session", autouse=True)
def setup_mock_auth():
    """Set up mock auth environment and populate USERS_DB for tests."""
    os.environ["MOCK_AUTH_USERNAME"] = "api_user"
    os.environ["MOCK_AUTH_PASSWORD"] = "change_me"
    settings.mock_auth_username = "api_user"
    settings.mock_auth_password = "change_me"
    USERS_DB.clear()
    _build_users_db_from_settings()
    yield


# ---------------------------------------------------------------------------
# BD SQLite en memoria para tests
# ---------------------------------------------------------------------------

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def db_session():
    """Sesión async sobre SQLite en memoria para tests de integración."""

    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


# ---------------------------------------------------------------------------
# Cliente HTTP con BD sobreescrita
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def async_client(db_session: AsyncSession, monkeypatch):
    """Cliente async con la BD en memoria inyectada y servicio ML mockeado."""

    app.dependency_overrides[get_db] = lambda: db_session
    
    # Mockear el cliente de ML para devolver un resultado válido
    async def mock_call_ml_predict(description: str, categoria: str):
        """Mock del cliente de ML que devuelve predicciones fijas."""
        return TicketClassificationResult(
            urgency=TicketUrgency.medium,
            category=TicketCategory.limpieza,
            model_name="mock-model",
            model_version="1.0.0",
        )
    
    monkeypatch.setattr(
        ticket_service,
        "call_ml_predict",
        mock_call_ml_predict,
    )
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Tokens de test
# ---------------------------------------------------------------------------


@pytest.fixture
def admin_token() -> str:
    """JWT firmado con rol admin para tests (usuario: api_user)."""
    return create_access_token({"sub": "api_user", "role": "admin"})


# ---------------------------------------------------------------------------
# Cliente síncrono (compatibilidad con tests legacy)
# ---------------------------------------------------------------------------


@pytest.fixture
def client(db_session: AsyncSession, monkeypatch) -> TestClient:
    """Cliente de pruebas síncrono para endpoints FastAPI (legacy).
    
    Sobrescribe la dependencia de BD con la sesión en memoria.
    """

    app.dependency_overrides[get_db] = lambda: db_session
    
    # Mockear el cliente de ML para devolver un resultado válido
    async def mock_call_ml_predict(description: str, categoria: str):
        """Mock del cliente de ML que devuelve predicciones fijas."""
        return TicketClassificationResult(
            urgency=TicketUrgency.medium,
            category=TicketCategory.limpieza,
            model_name="mock-model",
            model_version="1.0.0",
        )
    
    monkeypatch.setattr(
        ticket_service,
        "call_ml_predict",
        mock_call_ml_predict,
    )
    
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()
