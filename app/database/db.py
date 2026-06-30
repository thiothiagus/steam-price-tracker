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
    Base.metadata.create_all(bind=engine)
    import sqlite3
    db_path = settings.DATABASE_URL.replace("sqlite:///", "./")
    try:
        con = sqlite3.connect(db_path)
        con.execute("ALTER TABLE tracked_items ADD COLUMN quantity INTEGER DEFAULT 1 NOT NULL")
        con.commit()
        con.close()
    except Exception:
        pass
