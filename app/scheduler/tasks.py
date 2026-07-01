import asyncio
import logging
import time
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.collectors.steam import collector
from app.config import settings
from app.services.collector_service import collect_all_prices
from app.models.models import TrackedItem
from app.database.db import SessionLocal

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def scheduled_collect() -> None:
    if collector.rate_limited_until > time.time():
        remaining = int(collector.rate_limited_until - time.time())
        logger.info("Coleta agendada adiada: rate limit ativo por mais %ds.", remaining)
        return
    logger.info("Coleta agendada iniciada.")
    await collect_all_prices(force=False)


def start_scheduler() -> None:
    if scheduler.running:
        logger.info("Scheduler já está rodando.")
        return
    
    scheduler.add_job(
        scheduled_collect,
        trigger=CronTrigger(minute=0),
        id="price_collection",
        name="Collect Steam Market Prices",
        replace_existing=True,
    )
    logger.info("Scheduler started. Collection at every hour (XX:00).")
    scheduler.start()
    logger.info("Scheduler está rodando: %s", scheduler.running)


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped.")
