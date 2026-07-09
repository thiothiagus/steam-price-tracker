import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from sqlalchemy.orm import Session

from app.database.db import SessionLocal
from app.models.models import TrackedItem
from app.utils.save_parser import SaveParser
from app.config import settings

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
    tbh_appid = settings.TBH_APPID

    try:
        # For TBH, do a full sync: remove ALL TBH items not in current save
        if tbh_appid in appids_in_save:
            tbh_save_keys = {
                k for k in save_item_keys if k[0] == tbh_appid
            }
            # Soft delete all TBH items not in current save
            now = datetime.now(timezone.utc)
            all_tbh_tracked = (
                db.query(TrackedItem)
                .filter(
                    TrackedItem.appid == tbh_appid,
                    TrackedItem.removed_at.is_(None),
                )
                .all()
            )
            for tracked in all_tbh_tracked:
                key = (tracked.appid, tracked.market_hash_name)
                if key not in tbh_save_keys:
                    tracked.removed_at = now
                    removed += 1
                    logger.info("Soft deleted TBH item: %s", tracked.market_hash_name)

            # Reactivate previously removed TBH items that are now in save
            reactivated_count = (
                db.query(TrackedItem)
                .filter(
                    TrackedItem.appid == tbh_appid,
                    TrackedItem.removed_at.isnot(None),
                    TrackedItem.market_hash_name.in_([k[1] for k in tbh_save_keys]),
                )
                .update({TrackedItem.removed_at: None}, synchronize_session=False)
            )
            reactivated = reactivated_count

        # For other appids, use existing logic
        other_appids = appids_in_save - {tbh_appid}
        if other_appids:
            all_tracked = (
                db.query(TrackedItem)
                .filter(
                    TrackedItem.appid.in_(other_appids),
                    TrackedItem.removed_at.is_(None),
                )
                .all()
            )
            tracked_by_key = {
                (t.appid, t.market_hash_name): t for t in all_tracked
            }

            now = datetime.now(timezone.utc)
            soft_deleted = (
                db.query(TrackedItem)
                .filter(
                    TrackedItem.appid.in_(other_appids),
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
                    TrackedItem.appid.in_(other_appids),
                    TrackedItem.removed_at.isnot(None),
                )
                .update({TrackedItem.removed_at: None}, synchronize_session=False)
            )
            reactivated += reactivated_count

        # Upsert all items from save
        for item in items_to_import:
            key = (item["appid"], item["market_hash_name"])
            existing = (
                db.query(TrackedItem)
                .filter(
                    TrackedItem.appid == item["appid"],
                    TrackedItem.market_hash_name == item["market_hash_name"],
                )
                .first()
            )

            if existing:
                if existing.removed_at is not None:
                    existing.removed_at = None
                    reactivated += 1
                    logger.info("Reactivated item: %s", item["market_hash_name"])

                needs_update = False
                if existing.quantity != item["quantity"]:
                    old_qty = existing.quantity
                    existing.quantity = item["quantity"]
                    needs_update = True
                    logger.info(
                        "Updated qty for %s: %s -> %s",
                        item["market_hash_name"], old_qty, item["quantity"],
                    )
                if existing.gear_type != item.get("gear_type"):
                    existing.gear_type = item.get("gear_type")
                    needs_update = True
                if existing.gear_level != item.get("gear_level"):
                    existing.gear_level = item.get("gear_level")
                    needs_update = True
                if existing.item_type != item.get("type"):
                    existing.item_type = item.get("type")
                    needs_update = True
                if existing.is_equipped != item.get("is_equipped", False):
                    existing.is_equipped = item.get("is_equipped", False)
                    needs_update = True
                if needs_update:
                    updated += 1
                else:
                    skipped += 1
                continue

            track = TrackedItem(
                appid=item["appid"],
                market_hash_name=item["market_hash_name"],
                item_type=item.get("type"),
                gear_type=item.get("gear_type"),
                gear_level=item.get("gear_level"),
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
