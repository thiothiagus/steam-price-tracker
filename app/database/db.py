import logging
from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.config import settings

logger = logging.getLogger(__name__)


engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


_LEGACY_COLUMNS: dict[str, str] = {
    "quantity": "INTEGER DEFAULT 1 NOT NULL",
    "item_type": "TEXT",
    "is_equipped": "INTEGER DEFAULT 0 NOT NULL",
    "removed_at": "TIMESTAMP",
}


def _ensure_legacy_columns(table_name: str) -> None:
    """Adiciona colunas legadas em bancos pre-existentes, idempotentemente.

    Novas instalações já obtêm as colunas via ``Base.metadata.create_all``;
    este helper cobre apenas migração de bancos antigos onde o schema
    divergiu do modelo atual.
    """
    if "sqlite" not in settings.DATABASE_URL:
        return

    db_path = Path(settings.DATABASE_URL.replace("sqlite:///", ""))
    if not db_path.exists():
        return

    import sqlite3

    inspector = inspect(engine)
    if table_name not in inspector.get_table_names():
        return

    existing = {col["name"] for col in inspector.get_columns(table_name)}
    to_add = [
        (name, ddl) for name, ddl in _LEGACY_COLUMNS.items() if name not in existing
    ]
    if not to_add:
        return

    con = sqlite3.connect(db_path)
    try:
        for name, ddl in to_add:
            sql = f"ALTER TABLE {table_name} ADD COLUMN {name} {ddl}"
            logger.warning("Adicionando coluna legada: %s", sql)
            con.execute(sql)
        con.commit()
    finally:
        con.close()


def init_db() -> None:
    from app.models import models
    Base.metadata.create_all(bind=engine)
    _ensure_legacy_columns("tracked_items")
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
