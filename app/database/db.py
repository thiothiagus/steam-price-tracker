from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.config import settings


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


def init_db() -> None:
    from app.models import models
    Base.metadata.create_all(bind=engine)
    import sqlite3
    db_path = settings.DATABASE_URL.replace("sqlite:///", "./")
    con = sqlite3.connect(db_path)
    try:
        con.execute("ALTER TABLE tracked_items ADD COLUMN quantity INTEGER DEFAULT 1 NOT NULL")
    except Exception:
        pass
    try:
        con.execute("ALTER TABLE tracked_items ADD COLUMN item_type TEXT")
    except Exception:
        pass
    try:
        con.execute("ALTER TABLE tracked_items ADD COLUMN is_equipped INTEGER DEFAULT 0 NOT NULL")
    except Exception:
        pass
    try:
        con.execute("ALTER TABLE tracked_items ADD COLUMN removed_at TIMESTAMP")
    except Exception:
        pass
    con.commit()
    con.close()
