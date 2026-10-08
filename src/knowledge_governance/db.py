"""Database/session factories for short, freshly authorized work units."""
from __future__ import annotations

import os

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import Session, sessionmaker


def make_engine(database_url: str | None = None) -> Engine:
    url = database_url or os.environ.get("DATABASE_URL")
    if not url:
        raise ValueError("DATABASE_URL is required")
    backend = make_url(url).get_backend_name()
    if backend == "mysql":
        engine = create_engine(
            url, pool_pre_ping=True, isolation_level="READ COMMITTED",
        )

        @event.listens_for(engine, "connect")
        def set_utc(dbapi_connection, _):
            with dbapi_connection.cursor() as cursor:
                cursor.execute("SET time_zone = '+00:00'")

        return engine
    if backend == "sqlite":
        engine = create_engine(url)

        @event.listens_for(engine, "connect")
        def enable_foreign_keys(dbapi_connection, _):
            dbapi_connection.execute("PRAGMA foreign_keys=ON")

        return engine
    raise ValueError("Only MySQL and SQLite are supported by the initial migrations")


def make_session_factory(engine: Engine) -> sessionmaker[Session]:
    # Services own write transactions; close the session after each request/work unit.
    return sessionmaker(engine, expire_on_commit=False)
