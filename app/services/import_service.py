import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from sqlalchemy.orm import Session

from app.database.db import SessionLocal
from app.models.models import TrackedItem
from app.utils.save_parser import SaveParser

logger = logging.getLogger(__name__)


def import_from_save(save_path: str | Path) -> dict:
    parser = SaveParser(save_path)
    items_to_import = list(parser.get_collected_items_for_import())

    if not items_to_import:
        return {"imported": 0, "skipped": 0, "items": [], "message": "Nenhum item negociável encontrado no save."}

    db: Session = SessionLocal()
    imported = 0
    skipped = 0
    updated = 0
    reactivated = 0
    removed = 0
    imported_items = []

    save_item_keys = {
        (item["appid"], item["market_hash_name"]) for item in items_to_import
    }
    appids_in_save = {item["appid"] for item in items_to_import}

    try:
        all_tracked = (
            db.query(TrackedItem)
            .filter(
                TrackedItem.appid.in_(appids_in_save),
                TrackedItem.removed_at.is_(None),
            )
            .all()
        )
        tracked_by_key = {
            (t.appid, t.market_hash_name): t for t in all_tracked
        }

        for item in items_to_import:
            key = (item["appid"], item["market_hash_name"])
            existing = tracked_by_key.get(key)

            if existing:
                if existing.quantity != item["quantity"]:
                    old_qty = existing.quantity
                    existing.quantity = item["quantity"]
                    updated += 1
                    logger.info(
                        "Updated qty for %s: %s -> %s",
                        item["market_hash_name"], old_qty, item["quantity"],
                    )
                else:
                    skipped += 1
                continue

            track = TrackedItem(
                appid=item["appid"],
                market_hash_name=item["market_hash_name"],
                item_type=item.get("type"),
                is_equipped=item.get("is_equipped", False),
                enabled=True,
                quantity=item["quantity"],
            )
            db.add(track)
            db.flush()
            db.refresh(track)
            imported += 1
            imported_items.append({
                "id": track.id,
                "appid": track.appid,
                "market_hash_name": track.market_hash_name,
                "item_key": item["item_key"],
                "name": item["name"],
                "grade": item["grade"],
                "type": item["type"],
                "quantity": item["quantity"],
            })
            logger.info(
                "Imported item: %s (appid=%s, qty=%s)",
                item["market_hash_name"],
                item["appid"],
                item["quantity"],
            )

        now = datetime.now(timezone.utc)
        soft_deleted = (
            db.query(TrackedItem)
            .filter(
                TrackedItem.appid.in_(appids_in_save),
                TrackedItem.removed_at.is_(None),
            )
            .all()
        )
        for tracked in soft_deleted:
            key = (tracked.appid, tracked.market_hash_name)
            if key not in save_item_keys:
                tracked.removed_at = now
                removed += 1
                logger.info("Soft deleted item: %s", tracked.market_hash_name)

        reactivated_count = (
            db.query(TrackedItem)
            .filter(
                TrackedItem.appid.in_(appids_in_save),
                TrackedItem.removed_at.isnot(None),
            )
            .update({TrackedItem.removed_at: None}, synchronize_session=False)
        )
        reactivated = reactivated_count

        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Error importing save file.")
        raise
    finally:
        db.close()

    return {
        "imported": imported,
        "skipped": skipped,
        "updated": updated,
        "reactivated": reactivated,
        "removed": removed,
        "total_found": len(items_to_import),
        "items": imported_items,
        "message": f"{imported} importados, {updated} atualizados, {skipped} já existentes, {reactivated} reativados, {removed} removidos.",
    }
