"""Inicialización de la base de datos.

Propósito: crear todas las tablas definidas en los modelos ORM al arrancar
el servicio. En un proyecto con Alembic esto se sustituiría por las migraciones.
"""

import logging

import bcrypt
from sqlalchemy import select, text

from src.db.models import Base, UserORM
from src.db.session import AsyncSessionLocal, engine

logger = logging.getLogger(__name__)


async def _create_default_admin() -> None:
    """Crea un usuario admin por defecto si no existe."""
    async with AsyncSessionLocal() as session:
        # Verificar si el admin ya existe
        result = await session.execute(
            select(UserORM).where(UserORM.email == "admin@example.com")
        )
        existing_admin = result.scalar_one_or_none()

        if existing_admin:
            logger.info("Usuario admin ya existe: admin@example.com")
            return

        # Crear admin por defecto
        password_hash = bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode()
        admin_user = UserORM(
            nombre="Administrador",
            apellidos="Sistema",
            nif="00000000A",
            telefono="666000000",
            email="admin@example.com",
            domicilio="Sistema",
            password_hash=password_hash,
            role="admin",
        )

        session.add(admin_user)
        await session.commit()
        logger.info("✓ Usuario admin creado: admin@example.com / admin123")


async def init_db() -> None:
    """Crea todas las tablas si no existen.

    Seguro de ejecutar en cada arranque: `CREATE TABLE IF NOT EXISTS`.
    """

    logger.info("Inicializando esquema de base de datos...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(
            text("ALTER TABLE tickets ADD COLUMN IF NOT EXISTS user_id INTEGER")
        )
        await conn.execute(
            text(
                "ALTER TABLE tickets ADD COLUMN IF NOT EXISTS anon_fingerprint VARCHAR(128)"
            )
        )
    logger.info("Esquema de base de datos listo.")

    # Crear admin por defecto
    await _create_default_admin()
