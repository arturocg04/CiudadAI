"""Pruebas de inicialización y coherencia del esquema de BD.

Propósito: verificar que el arranque del sistema crea el esquema de BD correctamente.
"""

import pytest
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import create_async_engine

from src.db.models import Base


@pytest.mark.asyncio
async def test_init_db_creates_schema_correctly():
    """Verifica que el esquema de BD se crea correctamente.

    Este test verifica que:
    1. Se puede crear un motor SQLite temporal
    2. El esquema se crea correctamente con Base.metadata
    3. Las tablas principales existen (users, tickets)
    """

    # Usar SQLite en memoria para este test
    database_url = "sqlite+aiosqlite:///:memory:"
    engine = create_async_engine(database_url, echo=False)

    try:
        # Crear las tablas iniciales
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        # Verificar que las tablas existen usando run_sync para evitar error de AsyncConnection
        def _check_tables(sync_conn):
            inspector = inspect(sync_conn)
            tables = set(inspector.get_table_names())
            return tables

        async with engine.begin() as conn:
            tables = await conn.run_sync(_check_tables)
            # Las tablas principales deben existir
            assert "users" in tables, "Table 'users' should exist"
            assert "tickets" in tables, "Table 'tickets' should exist"

    finally:
        await engine.dispose()
