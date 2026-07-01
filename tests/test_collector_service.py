"""
Tests for collector service.
"""
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

from sqlalchemy.orm import Session

from app.services.collector_service import collect_all_prices, collect_single_item
from app.models.models import TrackedItem, PriceHistory
from app.collectors.steam import collector


@pytest.mark.asyncio
class TestCollectAllPrices:
    """Test collect_all_prices function."""

    async def test_collect_all_prices_no_items(self, test_db_session: Session, monkeypatch):
        """Test collection when no items are tracked."""
        monkeypatch.setattr("app.database.db.SessionLocal", lambda: test_db_session)
        
        result = await collect_all_prices(force=True)
        
        assert result["success"] is True
        assert result["collected"] == 0

    async def test_collect_all_prices_success(self, test_db_session: Session, sample_tracked_item, monkeypatch):
        """Test successful price collection."""
        monkeypatch.setattr("app.database.db.SessionLocal", lambda: test_db_session)
        
        mock_fetch = AsyncMock(return_value={
            "success": True,
            "lowest_price": 150.0,
            "median_price": 155.0,
            "volume": 100,
        })
        monkeypatch.setattr(collector, "fetch_price", mock_fetch)
        
        result = await collect_all_prices(force=True)
        
        assert result["success"] is True
        assert result["collected"] == 1
        assert mock_fetch.called
        
        records = test_db_session.query(PriceHistory).filter(
            PriceHistory.tracked_item_id == sample_tracked_item.id
        ).all()
        assert len(records) == 1
        assert records[0].price == 150.0

    async def test_collect_all_prices_steam_failure(self, test_db_session: Session, sample_tracked_item, monkeypatch):
        """Test collection when Steam API fails."""
        monkeypatch.setattr("app.database.db.SessionLocal", lambda: test_db_session)
        
        mock_fetch = AsyncMock(return_value={"success": False})
        monkeypatch.setattr(collector, "fetch_price", mock_fetch)
        
        result = await collect_all_prices(force=True)
        
        assert result["success"] is True
        assert result["collected"] == 0
        
        records = test_db_session.query(PriceHistory).filter(
            PriceHistory.tracked_item_id == sample_tracked_item.id
        ).all()
        assert len(records) == 0

    async def test_collect_all_prices_rate_limit(self, test_db_session: Session, sample_tracked_item, monkeypatch):
        """Test collection when rate limited."""
        monkeypatch.setattr("app.database.db.SessionLocal", lambda: test_db_session)
        monkeypatch.setattr(collector, "rate_limited_until", 9999999999)
        
        result = await collect_all_prices(force=True)
        
        assert result["success"] is False
        assert "Rate limit" in result.get("message", "")
        assert "cooldown_remaining" in result

    async def test_collect_all_prices_respects_refresh_hours(self, test_db_session: Session, sample_tracked_item, monkeypatch):
        """Test that collection respects refresh hours setting."""
        monkeypatch.setattr("app.database.db.SessionLocal", lambda: test_db_session)
        monkeypatch.setattr("app.services.collector_service.REFRESH_HOURS", 1)
        
        recent_record = PriceHistory(
            tracked_item_id=sample_tracked_item.id,
            price=100.0,
            median_price=105.0,
            volume=50,
            collected_at=datetime.now(timezone.utc) - timedelta(minutes=30),
        )
        test_db_session.add(recent_record)
        test_db_session.commit()
        
        result = await collect_all_prices(force=False)
        
        assert result["success"] is True
        assert result["collected"] == 0
        assert "atualizados" in result.get("message", "")

    async def test_collect_all_prices_force_ignores_refresh_hours(self, test_db_session: Session, sample_tracked_item, monkeypatch):
        """Test that force=True ignores refresh hours."""
        monkeypatch.setattr("app.database.db.SessionLocal", lambda: test_db_session)
        monkeypatch.setattr("app.services.collector_service.REFRESH_HOURS", 1)
        
        recent_record = PriceHistory(
            tracked_item_id=sample_tracked_item.id,
            price=100.0,
            median_price=105.0,
            volume=50,
            collected_at=datetime.now(timezone.utc) - timedelta(minutes=30),
        )
        test_db_session.add(recent_record)
        test_db_session.commit()
        
        mock_fetch = AsyncMock(return_value={
            "success": True,
            "lowest_price": 150.0,
            "median_price": 155.0,
            "volume": 100,
        })
        monkeypatch.setattr(collector, "fetch_price", mock_fetch)
        
        result = await collect_all_prices(force=True)
        
        assert result["success"] is True
        assert result["collected"] == 1


@pytest.mark.asyncio
class TestCollectSingleItem:
    """Test collect_single_item function."""

    async def test_collect_single_item_success(self, test_db_session: Session, sample_tracked_item, monkeypatch):
        """Test successful single item collection."""
        monkeypatch.setattr("app.database.db.SessionLocal", lambda: test_db_session)
        
        mock_fetch = AsyncMock(return_value={
            "success": True,
            "lowest_price": 175.0,
            "median_price": 180.0,
            "volume": 200,
        })
        monkeypatch.setattr(collector, "fetch_price", mock_fetch)
        
        result = await collect_single_item(sample_tracked_item.id)
        
        assert result is not None
        assert result["success"] is True
        assert result["lowest_price"] == 175.0
        
        records = test_db_session.query(PriceHistory).filter(
            PriceHistory.tracked_item_id == sample_tracked_item.id
        ).all()
        assert len(records) == 1
        assert records[0].price == 175.0

    async def test_collect_single_item_not_found(self, test_db_session: Session, monkeypatch):
        """Test collection for non-existent item."""
        monkeypatch.setattr("app.database.db.SessionLocal", lambda: test_db_session)
        
        result = await collect_single_item(99999)
        
        assert result is None

    async def test_collect_single_item_steam_failure(self, test_db_session: Session, sample_tracked_item, monkeypatch):
        """Test collection when Steam API fails."""
        monkeypatch.setattr("app.database.db.SessionLocal", lambda: test_db_session)
        
        mock_fetch = AsyncMock(return_value={"success": False})
        monkeypatch.setattr(collector, "fetch_price", mock_fetch)
        
        result = await collect_single_item(sample_tracked_item.id)
        
        assert result is not None
        assert result["success"] is False
        
        records = test_db_session.query(PriceHistory).filter(
            PriceHistory.tracked_item_id == sample_tracked_item.id
        ).all()
        assert len(records) == 0