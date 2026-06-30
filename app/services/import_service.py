import logging
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
    imported_items = []

    try:
        for item in items_to_import:
            existing = (
                db.query(TrackedItem)
                .filter(
                    TrackedItem.appid == item["appid"],
                    TrackedItem.market_hash_name == item["market_hash_name"],
                )
                .first()
            )
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
        "total_found": len(items_to_import),
        "items": imported_items,
        "message": f"{imported} importados, {updated} atualizados, {skipped} já existentes.",
    }
