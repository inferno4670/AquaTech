from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


# libpq-style query parameters that a managed Postgres dashboard (Supabase included)
# puts in the connection string but that asyncpg does not understand. SQLAlchemy forwards
# unrecognised URL query params straight through as connect() keyword arguments, so
# leaving `sslmode` in place fails with "connect() got an unexpected keyword argument".
_LIBPQ_ONLY_PARAMS = frozenset({"sslmode", "channel_binding", "options", "target_session_attrs"})


def _prepare_async_url(raw_url: str, schema: str = "") -> tuple[str, dict]:
    """Normalise a Postgres URL for asyncpg, or pass SQLite through untouched."""
    if not raw_url.startswith("postgres"):
        return raw_url, {}

    url = make_url(raw_url)
    query = {k: v for k, v in (url.query or {}).items() if k not in _LIBPQ_ONLY_PARAMS}

    connect_args: dict = {}
    # Managed Postgres providers (Supabase, Neon, RDS) require TLS and refuse plaintext
    # connections. asyncpg wants either `ssl=<mode>` or an SSLContext; "require" matches
    # what the libpq `sslmode=require` the dashboard hands you actually means.
    requested = (url.query or {}).get("sslmode")
    if requested in (None, "require", "prefer"):
        connect_args["ssl"] = "require"

    if schema:
        # Set search_path on the connection instead of stamping `schema=` onto every
        # table in models.py. That keeps the models portable: the same metadata still
        # creates plain unqualified tables on SQLite, and `create_all` here resolves
        # unqualified names into the chosen schema. `public` stays on the path so
        # extensions and helper functions defined there still resolve.
        connect_args["server_settings"] = {"search_path": f"{schema},public"}

    clean = url.set(query=query)
    # render_as_string(hide_password=False) keeps the credentials intact.
    return clean.render_as_string(hide_password=False), connect_args


def make_engine():
    settings = get_settings()
    url, connect_args = _prepare_async_url(settings.database_url_async, settings.database_schema)
    return create_async_engine(
        url,
        echo=settings.database_echo,
        pool_pre_ping=True,
        connect_args=connect_args,
    )


def make_session_maker() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(make_engine(), class_=AsyncSession, expire_on_commit=False)


SessionLocal = make_session_maker()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
