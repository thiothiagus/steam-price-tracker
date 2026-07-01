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


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    logger.info("Database initialized.")
    
    start_scheduler()
    import app.state as state
    from app.scheduler.tasks import scheduler
    logger.info("Scheduler status after start: running=%s", scheduler.running)
    
    logger.info("Iniciando coleta inicial dos preços (apenas itens > 1h sem atualização)...")
    from app.services.collector_service import collect_all_prices
    await collect_all_prices(force=False)
    logger.info("Coleta inicial concluída.")

    watcher = SaveWatcher(
        source_path=settings.save_source_path,
        dest_path=settings.save_dest_path,
        cooldown_seconds=settings.SAVE_WATCHER_COOLDOWN_SECONDS,
        poll_interval=settings.SAVE_WATCHER_POLL_INTERVAL,
    )
    state.save_watcher = watcher
    watcher.start()
    logger.info("SaveWatcher started.")

    yield
    logger.info("Shutting down...")
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
