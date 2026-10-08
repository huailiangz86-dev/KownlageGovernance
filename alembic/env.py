"""Alembic environment; online migrations require an explicit URL or connection."""
from __future__ import annotations

import os

from alembic import context

from knowledge_governance.db import make_engine
from knowledge_governance.models import Base

config = context.config
target_metadata = Base.metadata


def configure_and_run(connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations() -> None:
    shared_connection = config.attributes.get("connection")
    if shared_connection is not None:
        configure_and_run(shared_connection)
        return
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is required for schema migrations")
    if context.is_offline_mode():
        context.configure(
            url=database_url, target_metadata=target_metadata,
            literal_binds=True, dialect_opts={"paramstyle": "named"},
        )
        with context.begin_transaction():
            context.run_migrations()
        return
    engine = make_engine(database_url)
    try:
        with engine.connect() as connection:
            configure_and_run(connection)
    finally:
        engine.dispose()


run_migrations()
