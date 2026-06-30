import asyncio
import logging
import time

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.collectors.steam import collector
from app.config import settings
from app.services.collector_service import collect_all_prices
from app.models.models import TrackedItem
from app.database.db import SessionLocal

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def _get_collection_interval() -> int:
    db = SessionLocal()
    try:
        count = db.query(TrackedItem).filter(TrackedItem.enabled.is_(True)).count()
    finally:
        db.close()

    if count <= 20:
        return 5
    elif count <= 100:
        return 15
    elif count <= 500:
        return 30
    return 60


async def scheduled_collect() -> None:
    if collector.rate_limited_until > time.time():
        remaining = int(collector.rate_limited_until - time.time())
        logger.info("Coleta agendada adiada: rate limit ativo por mais %ds.", remaining)
        return
    logger.info("Coleta agendada iniciada.")
    await collect_all_prices(force=False)


def start_scheduler() -> None:
    interval_minutes = _get_collection_interval()
    scheduler.add_job(
        scheduled_collect,
        trigger=IntervalTrigger(minutes=interval_minutes),
        id="price_collection",
        name="Collect Steam Market Prices",
        replace_existing=True,
    )
    logger.info(
        "Scheduler started. Collection every %s minutes.", interval_minutes
    )
    scheduler.start()


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped.")
