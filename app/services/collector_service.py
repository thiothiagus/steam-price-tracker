import logging
import time
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.database.db import SessionLocal
from app.models.models import TrackedItem, PriceHistory
from app.collectors.steam import collector
from app.config import settings

logger = logging.getLogger(__name__)

REFRESH_HOURS = settings.COLLECTOR_REFRESH_HOURS


def _get_items_to_collect(db: Session, force: bool = False) -> list[TrackedItem]:
    items = db.query(TrackedItem).filter(TrackedItem.enabled.is_(True)).all()
    if force:
        return items

    cutoff = datetime.now(timezone.utc) - timedelta(hours=REFRESH_HOURS)
    to_collect = []
    for item in items:
        latest = (
            db.query(PriceHistory)
            .filter(PriceHistory.tracked_item_id == item.id)
            .order_by(PriceHistory.collected_at.desc())
            .first()
        )
        if latest is None:
            to_collect.append(item)
        elif latest.collected_at.tzinfo is None:
            collected_at = latest.collected_at.replace(tzinfo=timezone.utc)
            if collected_at < cutoff:
                to_collect.append(item)
        elif latest.collected_at < cutoff:
            to_collect.append(item)
    return to_collect


async def collect_all_prices(force: bool = False) -> dict:
    now = time.time()
    if force and collector.rate_limited_until > now:
        remaining = int(collector.rate_limited_until - now)
        msg = f"Rate limit ativo. Aguarde {remaining}s antes de coletar novamente."
        logger.warning(msg)
        return {"success": False, "message": msg, "cooldown_remaining": remaining}

    db: Session = SessionLocal()
    try:
        items = _get_items_to_collect(db, force=force)
        if not items:
            msg = "Todos os itens já foram atualizados nas últimas %d horas." % REFRESH_HOURS
            logger.info(msg)
            from app.state import collection_state
            collection_state = {"collecting": False, "collected": 0, "total": 0, "last_collection": True}
            return {"success": True, "message": msg, "collected": 0, "total": 0}

        logger.info(
            "Coletando preços: %s itens (%s itens no total)",
            len(items), db.query(TrackedItem).filter(TrackedItem.enabled.is_(True)).count(),
        )

        from app.state import collection_state
        collection_state = {"collecting": True, "collected": 0, "total": len(items)}

        collected = 0
        for item in items:
            if collector.rate_limited_until > time.time():
                logger.warning("Rate limit atingido. Coleta interrompida.")
                collection_state["collecting"] = False
                break

            result = await collector.fetch_price(item.appid, item.market_hash_name)
            if result.get("success"):
                record = PriceHistory(
                    tracked_item_id=item.id,
                    price=result["lowest_price"],
                    median_price=result["median_price"],
                    volume=result["volume"],
                    collected_at=datetime.now(timezone.utc),
                )
                db.add(record)
                collected += 1
                collection_state["collected"] = collected
                logger.info(
                    "  [%d/%d] %s: R$ %.2f (vol=%s)",
                    collected, len(items),
                    item.market_hash_name,
                    result.get("lowest_price", 0) or 0,
                    result.get("volume", "N/A"),
                )

        db.commit()
        msg = f"{collected}/{len(items)} itens coletados."
        if collected < len(items):
            msg += " Coleta interrompida por rate limit."

        collection_state = {"collecting": False, "collected": collected, "total": len(items), "last_collection": True}
        logger.info("Coleta finalizada: %s", msg)
        return {"success": True, "message": msg, "collected": collected, "total": len(items)}

    except Exception:
        db.rollback()
        logger.exception("Erro durante coleta de preços.")
        from app.state import collection_state
        collection_state = {"collecting": False, "collected": 0, "total": 0}
        return {"success": False, "message": "Erro interno durante coleta."}
    finally:
        db.close()


async def collect_single_item(item_id: int) -> dict | None:
    db: Session = SessionLocal()
    try:
        item = db.query(TrackedItem).filter(TrackedItem.id == item_id).first()
        if not item:
            return None

        result = await collector.fetch_price(item.appid, item.market_hash_name)
        if result.get("success"):
            record = PriceHistory(
                tracked_item_id=item.id,
                price=result["lowest_price"],
                median_price=result["median_price"],
                volume=result["volume"],
                collected_at=datetime.now(timezone.utc),
            )
            db.add(record)
            db.commit()
            return result
        return result
    except Exception:
        db.rollback()
        logger.exception("Error collecting single item.")
        return None
    finally:
        db.close()
