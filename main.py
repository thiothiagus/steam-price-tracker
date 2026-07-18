import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database.db import init_db
from app.scheduler.tasks import start_scheduler, stop_scheduler
from app.services.save_watcher import SaveWatcher
from app.api.routes import router as api_router
from app.api.pages import router as pages_router

logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def _initial_price_collection() -> None:
    try:
        from app.services.collector_service import collect_all_prices

        logger.info(
            "Iniciando coleta inicial dos preços em background "
            "(apenas itens > 1h sem atualização)..."
        )
        await collect_all_prices(force=False)
        logger.info("Coleta inicial concluída.")
    except Exception:
        logger.exception("Falha durante coleta inicial em background.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    logger.info("Database initialized.")

    start_scheduler()
    import app.state as state
    from app.scheduler.tasks import scheduler
    logger.info("Scheduler status after start: running=%s", scheduler.running)

    initial_collect_task: asyncio.Task | None = None
    if settings.RUN_INITIAL_COLLECTION_ON_STARTUP:
        initial_collect_task = asyncio.create_task(
            _initial_price_collection(),
            name="initial-price-collection",
        )

    watcher = SaveWatcher(
        source_path=settings.save_source_path,
        dest_path=settings.save_dest_path,
        cooldown_seconds=settings.SAVE_WATCHER_COOLDOWN_SECONDS,
        poll_interval=settings.SAVE_WATCHER_POLL_INTERVAL,
    )
    state.save_watcher = watcher
    watcher.start()
    logger.info("SaveWatcher started.")

    try:
        yield
    finally:
        logger.info("Shutting down...")
        if initial_collect_task is not None and not initial_collect_task.done():
            initial_collect_task.cancel()
            try:
                await initial_collect_task
            except (asyncio.CancelledError, Exception):
                pass
        watcher.stop()
        stop_scheduler()
        from app.collectors.steam import collector

        await collector.close()


app = FastAPI(title="Steam Market Price Tracker", lifespan=lifespan)

app.mount(
    "/static",
    StaticFiles(directory=str(settings.BASE_DIR / "frontend" / "static")),
    name="static",
)

app.include_router(api_router)
app.include_router(pages_router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
