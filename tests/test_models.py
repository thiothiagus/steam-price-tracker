"""
Tests for database and models.
"""
import pytest
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.models import TrackedItem, PriceHistory


class TestTrackedItemModel:
    """Test TrackedItem model."""

    def test_create_tracked_item(self, test_db_session: Session):
        """Test creating a tracked item."""
        item = TrackedItem(
            appid=730,
            market_hash_name="AK-47 | Redline (Field-Tested)",
            enabled=True,
            quantity=1,
        )
        test_db_session.add(item)
        test_db_session.commit()
        test_db_session.refresh(item)
        
        assert item.id is not None
        assert item.appid == 730
        assert item.market_hash_name == "AK-47 | Redline (Field-Tested)"
        assert item.enabled is True
        assert item.quantity == 1
        assert item.created_at is not None

    def test_tracked_item_repr(self, test_db_session: Session):
        """Test TrackedItem string representation."""
        item = TrackedItem(
            appid=730,
            market_hash_name="Test Item",
            enabled=True,
        )
        test_db_session.add(item)
        test_db_session.commit()
        
        assert "Test Item" in repr(item)
        assert "730" in repr(item)

    def test_tracked_item_default_values(self, test_db_session: Session):
        """Test TrackedItem default values."""
        item = TrackedItem(
            appid=730,
            market_hash_name="Test Item",
        )
        test_db_session.add(item)
        test_db_session.commit()
        
        assert item.enabled is True
        assert item.quantity == 1


class TestPriceHistoryModel:
    """Test PriceHistory model."""

    def test_create_price_history(self, test_db_session: Session, sample_tracked_item):
        """Test creating a price history record."""
        record = PriceHistory(
            tracked_item_id=sample_tracked_item.id,
            price=150.0,
            median_price=155.0,
            volume=100,
            collected_at=datetime.now(timezone.utc),
        )
        test_db_session.add(record)
        test_db_session.commit()
        test_db_session.refresh(record)
        
        assert record.id is not None
        assert record.price == 150.0
        assert record.median_price == 155.0
        assert record.volume == 100
        assert record.tracked_item_id == sample_tracked_item.id

    def test_price_history_repr(self, test_db_session: Session, sample_tracked_item):
        """Test PriceHistory string representation."""
        record = PriceHistory(
            tracked_item_id=sample_tracked_item.id,
            price=150.0,
            median_price=155.0,
            volume=100,
        )
        test_db_session.add(record)
        test_db_session.commit()
        
        assert "150.0" in repr(record)
        assert str(sample_tracked_item.id) in repr(record)

    def test_price_history_nullable_fields(self, test_db_session: Session, sample_tracked_item):
        """Test that price fields can be nullable."""
        record = PriceHistory(
            tracked_item_id=sample_tracked_item.id,
            price=None,
            median_price=None,
            volume=None,
        )
        test_db_session.add(record)
        test_db_session.commit()
        
        assert record.price is None
        assert record.median_price is None
        assert record.volume is None


class TestRelationships:
    """Test model relationships."""

    def test_tracked_item_has_price_records(self, test_db_session: Session, sample_tracked_item, sample_price_history):
        """Test that tracked item has associated price records."""
        test_db_session.refresh(sample_tracked_item)
        
        assert len(sample_tracked_item.price_records) == 2
        assert all(
            record.tracked_item_id == sample_tracked_item.id
            for record in sample_tracked_item.price_records
        )

    def test_price_history_has_tracked_item(self, test_db_session: Session, sample_tracked_item, sample_price_history):
        """Test that price history record has associated tracked item."""
        for record in sample_price_history:
            test_db_session.refresh(record)
            assert record.tracked_item.id == sample_tracked_item.id
            assert record.tracked_item.market_hash_name == sample_tracked_item.market_hash_name

    def test_cascade_delete(self, test_db_session: Session, sample_tracked_item, sample_price_history):
        """Test that deleting a tracked item cascades to price history."""
        item_id = sample_tracked_item.id
        
        test_db_session.delete(sample_tracked_item)
        test_db_session.commit()
        
        remaining_records = test_db_session.query(PriceHistory).filter(
            PriceHistory.tracked_item_id == item_id
        ).all()
        assert len(remaining_records) == 0