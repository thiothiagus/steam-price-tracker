"""Tests for analytics_service.compute_item_analytics."""
from datetime import datetime, timedelta, timezone

from app.models.models import TrackedItem, PriceHistory
from app.services.analytics_service import compute_item_analytics


def _now() -> datetime:
    return datetime(2026, 7, 2, 12, 0, tzinfo=timezone.utc)


def test_analytics_with_no_records(test_db_session):
    item = TrackedItem(appid=730, market_hash_name="AK-47 | X", quantity=1)
    test_db_session.add(item)
    test_db_session.commit()
    test_db_session.refresh(item)

    result = compute_item_analytics(test_db_session, item, now=_now())

    assert result["latest_price"] is None
    assert result["change_24h_pct"] is None
    assert result["moving_avg_7d"] is None
    assert result["min_24h"] is None
    assert result["max_24h"] is None
    assert result["sample_count"] == 0
    assert result["sparkline"] == []


def test_analytics_24h_change_positive(test_db_session):
    item = TrackedItem(appid=730, market_hash_name="AK-47 | Y", quantity=1)
    test_db_session.add(item)
    test_db_session.commit()
    test_db_session.refresh(item)

    now = _now()
    test_db_session.add_all(
        [
            PriceHistory(
                tracked_item_id=item.id,
                price=100.0,
                collected_at=now - timedelta(hours=48),
            ),
            PriceHistory(
                tracked_item_id=item.id,
                price=110.0,
                collected_at=now - timedelta(hours=23),
            ),
            PriceHistory(
                tracked_item_id=item.id,
                price=121.0,
                collected_at=now - timedelta(hours=1),
            ),
        ]
    )
    test_db_session.commit()

    result = compute_item_analytics(test_db_session, item, now=now)

    assert result["latest_price"] == 121.0
    assert result["sample_count"] == 3
    assert result["min_24h"] == 110.0
    assert result["max_24h"] == 121.0
    assert result["change_24h_pct"] == 10.0
    assert result["moving_avg_7d"] is not None


def test_analytics_change_24h_handles_missing_first_price(test_db_session):
    item = TrackedItem(appid=730, market_hash_name="AK-47 | Z", quantity=1)
    test_db_session.add(item)
    test_db_session.commit()
    test_db_session.refresh(item)

    now = _now()
    test_db_session.add(
        PriceHistory(
            tracked_item_id=item.id,
            price=200.0,
            collected_at=now - timedelta(hours=2),
        )
    )
    test_db_session.commit()

    result = compute_item_analytics(test_db_session, item, now=now)
    assert result["latest_price"] == 200.0
    assert result["min_24h"] == 200.0
    assert result["max_24h"] == 200.0
    assert result["change_24h_pct"] == 0.0


def test_analytics_change_24h_handles_zero_baseline(test_db_session):
    item = TrackedItem(appid=730, market_hash_name="AK-47 | W", quantity=1)
    test_db_session.add(item)
    test_db_session.commit()
    test_db_session.refresh(item)

    now = _now()
    test_db_session.add_all(
        [
            PriceHistory(
                tracked_item_id=item.id,
                price=0.0,
                collected_at=now - timedelta(hours=23),
            ),
            PriceHistory(
                tracked_item_id=item.id,
                price=10.0,
                collected_at=now - timedelta(hours=1),
            ),
        ]
    )
    test_db_session.commit()

    result = compute_item_analytics(test_db_session, item, now=now)
    assert result["latest_price"] == 10.0
    assert result["change_24h_pct"] is None


def test_analytics_returns_sparkline_last_30(test_db_session):
    item = TrackedItem(appid=730, market_hash_name="AK-47 | V", quantity=1)
    test_db_session.add(item)
    test_db_session.commit()
    test_db_session.refresh(item)

    now = _now()
    for i in range(40):
        test_db_session.add(
            PriceHistory(
                tracked_item_id=item.id,
                price=100.0 + i,
                collected_at=now - timedelta(hours=i),
            )
        )
    test_db_session.commit()

    result = compute_item_analytics(test_db_session, item, now=now)
    assert len(result["sparkline"]) == 30
    sorted_spark = sorted(result["sparkline"], key=lambda p: p["t"])
    timestamps = [p["t"] for p in sorted_spark]
    assert timestamps == sorted(timestamps)
