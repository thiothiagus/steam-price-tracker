"""
Test fixtures for Steam Price Tracker tests.
"""
import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime, timezone

from app.database.db import Base, get_db
from app.models.models import TrackedItem, PriceHistory


@pytest.fixture
def test_db_engine():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_db_session_factory(test_db_engine):
    """Create a test database session factory."""
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_db_engine,
    )
    return TestingSessionLocal


@pytest.fixture
def test_db_session(test_db_session_factory):
    """Create a test database session."""
    session = test_db_session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def sample_tracked_item(test_db_session: Session):
    """Create a sample tracked item for testing."""
    item = TrackedItem(
        appid=730,
        market_hash_name="AK-47 | Redline (Field-Tested)",
        enabled=True,
        quantity=1,
    )
    test_db_session.add(item)
    test_db_session.commit()
    test_db_session.refresh(item)
    return item


@pytest.fixture
def sample_price_history(test_db_session: Session, sample_tracked_item: TrackedItem):
    """Create sample price history records for testing."""
    records = [
        PriceHistory(
            tracked_item_id=sample_tracked_item.id,
            price=150.0,
            median_price=155.0,
            volume=100,
            collected_at=datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc),
        ),
        PriceHistory(
            tracked_item_id=sample_tracked_item.id,
            price=160.0,
            median_price=165.0,
            volume=120,
            collected_at=datetime(2024, 1, 2, 12, 0, tzinfo=timezone.utc),
        ),
    ]
    for record in records:
        test_db_session.add(record)
    test_db_session.commit()
    return records


@pytest.fixture
def db_override(test_db_session_factory):
    """Override get_db dependency for FastAPI tests."""
    def _get_db():
        session = test_db_session_factory()
        try:
            yield session
        finally:
            session.close()
    return _get_db


@pytest.fixture
def collector_session_factory(test_db_session_factory):
    """Session factory for collector service tests."""
    return test_db_session_factory