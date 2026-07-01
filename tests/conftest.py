"""
Test fixtures for Steam Price Tracker tests.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database.db import Base, get_db
from app.models.models import TrackedItem, PriceHistory


@pytest.fixture
def test_db_engine():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_db_session(test_db_engine):
    """Create a test database session."""
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_db_engine,
    )
    session = TestingSessionLocal()
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
    from datetime import datetime, timezone
    
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
def db_override(test_db_session: Session):
    """Override get_db dependency for FastAPI tests."""
    def _get_db():
        try:
            yield test_db_session
        finally:
            pass
    
    return _get_db