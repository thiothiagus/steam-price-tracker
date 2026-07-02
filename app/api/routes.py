import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.models.models import TrackedItem, PriceHistory
from app.schemas import (
    TrackedItemCreate,
    TrackedItemResponse,
    PriceHistoryResponse,
    PriceCollectResponse,
)
from app.collectors.steam import collector
from app.services.collector_service import collect_single_item

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["api"])


@router.get("/items", response_model=List[TrackedItemResponse])
def list_items(db: Session = Depends(get_db)):
    items = (
        db.query(TrackedItem)
        .filter(TrackedItem.removed_at.is_(None))
        .order_by(TrackedItem.id.desc())
        .all()
    )
    return items


@router.get("/items/archived", response_model=List[TrackedItemResponse])
def list_archived_items(db: Session = Depends(get_db)):
    items = (
        db.query(TrackedItem)
        .filter(TrackedItem.removed_at.isnot(None))
        .order_by(TrackedItem.removed_at.desc())
        .all()
    )
    return items


@router.post("/items/{item_id}/restore", response_model=TrackedItemResponse)
def restore_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(TrackedItem).filter(TrackedItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found.")
    item.removed_at = None
    db.commit()
    db.refresh(item)
    return item


@router.post("/items", response_model=TrackedItemResponse, status_code=201)
def create_item(data: TrackedItemCreate, db: Session = Depends(get_db)):
    existing = (
        db.query(TrackedItem)
        .filter(
            TrackedItem.appid == data.appid,
            TrackedItem.market_hash_name == data.market_hash_name.strip(),
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="Item already tracked.")

    item = TrackedItem(
        appid=data.appid,
        market_hash_name=data.market_hash_name.strip(),
        enabled=data.enabled,
        created_at=datetime.now(timezone.utc),
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    logger.info("Created tracked item: %s (appid=%s)", data.market_hash_name, data.appid)
    return item


@router.delete("/items/{item_id}", status_code=204)
def delete_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(TrackedItem).filter(TrackedItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found.")
    db.delete(item)
    db.commit()


@router.patch("/items/{item_id}/toggle", response_model=TrackedItemResponse)
def toggle_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(TrackedItem).filter(TrackedItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found.")
    item.enabled = not item.enabled
    db.commit()
    db.refresh(item)
    return item


@router.get("/items/{item_id}/history", response_model=List[PriceHistoryResponse])
def get_price_history(item_id: int, limit: int = 100, db: Session = Depends(get_db)):
    item = db.query(TrackedItem).filter(TrackedItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found.")

    records = (
        db.query(PriceHistory)
        .filter(PriceHistory.tracked_item_id == item_id)
        .order_by(PriceHistory.collected_at.desc())
        .limit(limit)
        .all()
    )
    return records


@router.post("/items/{item_id}/collect", response_model=PriceCollectResponse)
async def collect_item_price(item_id: int):
    result = await collect_single_item(item_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Item not found.")
    return PriceCollectResponse(**result)


@router.post("/collect")
async def trigger_collection():
    from app.services.collector_service import collect_all_prices
    result = await collect_all_prices(force=True)
    if not result.get("success"):
        raise HTTPException(status_code=429, detail=result.get("message", "Rate limited"))
    return {"message": result.get("message", "Collection started.")}


@router.get("/collect/cooldown")
def collection_cooldown():
    now = time.time()
    remaining = max(0, int(collector.rate_limited_until - now))
    return {"rate_limited": remaining > 0, "cooldown_remaining": remaining}


@router.post("/import-save")
def import_save():
    from app.services.import_service import import_from_save
    from app.config import settings

    save_path = settings.BASE_DIR / "SaveFile_Live.es3"
    if not save_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Save file not found. Copy SaveFile_Live.es3 to the project root.",
        )

    result = import_from_save(save_path)
    return result


@router.get("/watcher/status")
def watcher_status():
    from app.state import save_watcher
    if save_watcher is None:
        return {"running": False, "error": "Watcher not initialized"}
    return {
        "running": save_watcher.is_running,
        "source_exists": save_watcher.source_exists,
        "source_path": str(save_watcher.source_path),
        "dest_path": str(save_watcher.dest_path),
        "error": save_watcher.error,
    }


@router.post("/watcher/start")
def watcher_start():
    from app.state import save_watcher
    if save_watcher is None:
        raise HTTPException(status_code=503, detail="Watcher not initialized")
    save_watcher.start()
    return {"message": "Save watcher started."}


@router.post("/watcher/stop")
def watcher_stop():
    from app.state import save_watcher
    if save_watcher is None:
        raise HTTPException(status_code=503, detail="Watcher not initialized")
    save_watcher.stop()
    return {"message": "Save watcher stopped."}


@router.get("/import-preview")
def import_preview():
    from app.utils.save_parser import SaveParser
    from app.config import settings

    save_path = settings.BASE_DIR / "SaveFile_Live.es3"
    if not save_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Save file not found. Copy SaveFile_Live.es3 to the project root.",
        )

    parser = SaveParser(save_path)
    items = list(parser.get_collected_items_for_import())

    from app.database.db import SessionLocal
    from app.models.models import TrackedItem

    db = SessionLocal()
    try:
        existing = set()
        for item in items:
            found = (
                db.query(TrackedItem)
                .filter(
                    TrackedItem.appid == item["appid"],
                    TrackedItem.market_hash_name == item["market_hash_name"],
                )
                .first()
            )
            if found:
                existing.add(item["market_hash_name"])

        for item in items:
            item["already_tracked"] = item["market_hash_name"] in existing
    finally:
        db.close()

    return {
        "total_tradable_items": len(items),
        "total_quantity": sum(i["quantity"] for i in items),
        "items": items,
    }


@router.get("/collection/status")
def collection_status():
    from app.state import collection_state
    if collection_state is None:
        return {"collecting": False, "collected": 0, "total": 0}
    return {
        "collecting": collection_state.get("collecting", False),
        "collected": collection_state.get("collected", 0),
        "total": collection_state.get("total", 0),
        "last_collection": collection_state.get("last_collection"),
    }
