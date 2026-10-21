"""Base declarativa, engine e sessão."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from ngeo.core.config import get_settings

#: Convenção de nomes para restrições previsíveis em migrações.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Base de todos os modelos ORM."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)


def build_engine(database_url: str | None = None, **kwargs: Any) -> Any:
    """Cria a engine. ``pool_pre_ping`` protege contra conexão morta (Docker)."""
    settings = get_settings()
    url = database_url or settings.database_url
    options: dict[str, Any] = {"pool_pre_ping": True, "future": True}
    options.update(kwargs)
    return create_engine(url, **options)


def build_session_factory(engine: Any) -> sessionmaker[Session]:
    """Fábrica de sessões."""
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)


@contextmanager
def session_scope(session_factory: sessionmaker[Session] | None = None) -> Iterator[Session]:
    """Sessão transacional (commit/rollback automático)."""
    if session_factory is None:
        session_factory = build_session_factory(build_engine())
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
