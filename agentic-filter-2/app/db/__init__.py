from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def configure_engine(url: str) -> None:
    global _engine, _session_factory
    _engine = create_engine(url, pool_pre_ping=True)
    _session_factory = sessionmaker(bind=_engine, autoflush=False, autocommit=False)


def dispose_engine() -> None:
    """Release the SQLAlchemy engine (e.g. app shutdown or isolated tests)."""
    global _engine, _session_factory
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _session_factory = None


def get_engine() -> Engine:
    if _engine is None:
        msg = "Database engine not configured; call configure_engine first"
        raise RuntimeError(msg)
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    if _session_factory is None:
        msg = "Database engine not configured; call configure_engine first"
        raise RuntimeError(msg)
    return _session_factory


def session_scope() -> Generator[Session, None, None]:
    factory = get_session_factory()
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
