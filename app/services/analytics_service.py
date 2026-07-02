"""Analytics for tracked items: 24h variation, 7-day moving average, etc."""
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.models import TrackedItem, PriceHistory


def _slice_by_age(
    records: list[PriceHistory], max_age: timedelta, now: datetime
) -> list[PriceHistory]:
    cutoff = now - max_age
    out = []
    for r in records:
        ts = r.collected_at
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        if ts >= cutoff:
            out.append(r)
    return out


def compute_item_analytics(
    db: Session, item: TrackedItem, now: datetime | None = None
) -> dict:
    """Compute price analytics for a single tracked item.

    Returns a dict with: latest, change_24h_pct, change_7d_pct, moving_avg_7d,
    min_24h, max_24h, vol_24h, sample_count, sparkline.
    """
    now = now or datetime.now(timezone.utc)

    records: list[PriceHistory] = (
        db.query(PriceHistory)
        .filter(PriceHistory.tracked_item_id == item.id)
        .order_by(PriceHistory.collected_at.asc())
        .all()
    )

    def _price_list(rs: list[PriceHistory]) -> list[float]:
        return [r.price for r in rs if r.price is not None]

    last_24h = _slice_by_age(records, timedelta(hours=24), now)
    last_7d = _slice_by_age(records, timedelta(days=7), now)

    prices_24h = _price_list(last_24h)
    prices_7d = _price_list(last_7d)
    all_prices = _price_list(records)

    latest_price = all_prices[-1] if all_prices else None
    moving_avg_7d = (
        round(sum(prices_7d) / len(prices_7d), 2) if prices_7d else None
    )

    def _pct_change(older: float | None, newer: float | None) -> float | None:
        if older is None or newer is None or older == 0:
            return None
        return round(((newer - older) / older) * 100.0, 2)

    change_24h_pct = (
        _pct_change(prices_24h[0], latest_price)
        if len(prices_24h) >= 1
        else None
    )
    change_7d_pct = (
        _pct_change(prices_7d[0], latest_price) if len(prices_7d) >= 1 else None
    )

    sparkline = [
        {"t": r.collected_at.isoformat(), "price": r.price}
        for r in records[-30:]
        if r.price is not None
    ]

    return {
        "latest_price": latest_price,
        "change_24h_pct": change_24h_pct,
        "change_7d_pct": change_7d_pct,
        "moving_avg_7d": moving_avg_7d,
        "min_24h": min(prices_24h) if prices_24h else None,
        "max_24h": max(prices_24h) if prices_24h else None,
        "vol_24h": sum(r.volume for r in last_24h if r.volume) or None,
        "sample_count": len(records),
        "sparkline": sparkline,
    }
