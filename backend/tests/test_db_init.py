"""Pruebas de inicialización y coherencia del esquema de BD.

Propósito: verificar que el arranque corrige esquemas locales incoherentes
antes de sembrar los datos base.
"""

from pathlib import Path

import pytest
from sqlalchemy import inspect, select, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.config import settings
from src.db import init_db as db_init
from src.db.models import Base, UserORM


@pytest.mark.asyncio
async def test_init_db_rebuilds_schema_when_columns_drift(tmp_path: Path, monkeypatch):
    """Si el esquema real difiere, init_db debe reconstruirlo en dev."""

    database_path = tmp_path / "ciudadia.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{database_path}")
    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False)

    monkeypatch.setattr(db_init, "engine", engine)
    monkeypatch.setattr(db_init, "AsyncSessionLocal", session_factory)
    monkeypatch.setattr(settings, "app_env", "dev")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(text("ALTER TABLE users ADD COLUMN legacy_flag TEXT"))

    async with engine.begin() as conn:
        assert await conn.run_sync(db_init._schema_matches) is False

    await db_init.init_db()

    async with engine.begin() as conn:
        assert await conn.run_sync(db_init._schema_matches) is True
        inspector = inspect(conn)
        assert "legacy_flag" not in {column["name"] for column in inspector.get_columns("users")}

    async with session_factory() as session:
        result = await session.execute(
            select(UserORM).where(UserORM.email == "admin@example.com")
        )
        admin_user = result.scalar_one_or_none()
        assert admin_user is not None
        assert admin_user.email == "admin@example.com"
        assert admin_user.role == "admin"

    await engine.dispose()
