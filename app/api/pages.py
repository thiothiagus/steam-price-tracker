from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import datetime, timedelta

from app.config import settings
from app.database.db import get_db
from app.models.models import TrackedItem, PriceHistory
from app.utils.item_db import get_item_by_market_name, get_grade_color, get_item_icon_url

router = APIRouter(tags=["pages"])
templates = Jinja2Templates(directory=str(settings.BASE_DIR / "frontend" / "templates"))

REFRESH_HOURS = settings.COLLECTOR_REFRESH_HOURS
STALE_CUTOFF = timedelta(hours=REFRESH_HOURS)
TBH_APPID = settings.TBH_APPID

MIN_PRICE_THRESHOLD = 1.0
FIXED_FEE = 0.10
FEE_MULTIPLIER = 0.87


def calculate_revenue(price: float) -> float:
    if price < MIN_PRICE_THRESHOLD:
        return max(0, price - FIXED_FEE)
    return price * FEE_MULTIPLIER


def _build_items_data(items: list[TrackedItem], db: Session) -> list[dict]:
    now = datetime.utcnow()
    cutoff = now - STALE_CUTOFF
    data = []
    for item in items:
        latest = (
            db.query(PriceHistory)
            .filter(PriceHistory.tracked_item_id == item.id)
            .order_by(PriceHistory.collected_at.desc())
            .first()
        )
        collected_at = latest.collected_at if latest else None
        if not collected_at:
            freshness = "pending"
        elif collected_at < cutoff:
            freshness = "stale"
        elif collected_at < now - timedelta(hours=6):
            freshness = "ok"
        else:
            freshness = "fresh"

        qty = item.quantity if item.quantity else 1
        unit_price = latest.price if latest else None
        total_price = (unit_price * qty) if unit_price else None

        grade = ""
        grade_color = ""
        icon_url = None
        has_icon = False
        item_type = item.item_type
        gear_type = None
        gear_level = None
        db_item = get_item_by_market_name(item.market_hash_name)
        if db_item:
            grade = db_item.get("grade", "")
            grade_color = get_grade_color(grade)
            if not item_type:
                item_type = db_item.get("type")
            if item_type == "GEAR":
                gear_type = db_item.get("gearType")
                gear_level = db_item.get("level")
        icon_url = get_item_icon_url(item.market_hash_name, item.appid)
        has_icon = icon_url is not None

        data.append({
            "id": item.id,
            "appid": item.appid,
            "is_tbh_app": item.appid == TBH_APPID,
            "market_hash_name": item.market_hash_name,
            "type": item_type,
            "gear_type": gear_type,
            "gear_level": gear_level,
            "is_equipped": item.is_equipped,
            "enabled": item.enabled,
            "quantity": qty,
            "grade": grade,
            "grade_color": grade_color,
            "icon_url": icon_url,
            "has_icon": has_icon,
            "latest_price": unit_price,
            "total_price": total_price,
            "latest_volume": latest.volume if latest else None,
            "collected_at": collected_at.isoformat() if collected_at else None,
            "freshness": freshness,
        })
    return data


def _stats(items: list[TrackedItem], db: Session) -> dict:
    total_items = len(items)
    active_items = sum(1 for i in items if i.enabled)

    total_inventory_value = 0.0
    total_inventory_value_after_fees = 0.0
    items_with_price = 0
    total_quantity = 0
    highest_value_item = None
    highest_value = 0.0

    for item in items:
        latest = (
            db.query(PriceHistory)
            .filter(PriceHistory.tracked_item_id == item.id)
            .order_by(PriceHistory.collected_at.desc())
            .first()
        )
        qty = item.quantity if item.quantity else 1
        total_quantity += qty

        if latest and latest.price:
            item_total = latest.price * qty
            total_inventory_value += item_total
            total_inventory_value_after_fees += calculate_revenue(latest.price) * qty
            items_with_price += 1

            if item_total > highest_value:
                highest_value = item_total
                highest_value_item = item.market_hash_name

    avg_item_price = total_inventory_value / items_with_price if items_with_price > 0 else 0

    return {
        "total_items": total_items,
        "active_items": active_items,
        "total_inventory_value": total_inventory_value,
        "total_inventory_value_after_fees": total_inventory_value_after_fees,
        "items_with_price": items_with_price,
        "total_quantity": total_quantity,
        "avg_item_price": avg_item_price,
        "highest_value_item": highest_value_item,
        "highest_value": highest_value,
    }


@router.get("/")
def dashboard(request: Request, db: Session = Depends(get_db)):
    items = (
        db.query(TrackedItem)
        .filter(TrackedItem.appid == TBH_APPID, TrackedItem.removed_at.is_(None))
        .order_by(TrackedItem.id.desc())
        .all()
    )
    items_data = _build_items_data(items, db)
    gears = [i for i in items_data if i.get("type") == "GEAR"]
    materials = [i for i in items_data if i.get("type") == "MATERIAL"]
    stats = _stats(items, db)
    return templates.TemplateResponse(
        "dashboard.html", {
            "request": request,
            "gears": gears,
            "materials": materials,
            "refresh_hours": REFRESH_HOURS,
            "stats": stats,
            "active_tab": "tbh",
        }
    )


@router.get("/cs2")
def dashboard_cs2(request: Request, db: Session = Depends(get_db)):
    items = (
        db.query(TrackedItem)
        .filter(TrackedItem.appid != TBH_APPID, TrackedItem.removed_at.is_(None))
        .order_by(TrackedItem.id.desc())
        .all()
    )
    items_data = _build_items_data(items, db)
    gears = [i for i in items_data if i.get("type") == "GEAR"]
    materials = [i for i in items_data if i.get("type") == "MATERIAL"]
    stats = _stats(items, db)
    return templates.TemplateResponse(
        "dashboard.html", {
            "request": request,
            "gears": gears,
            "materials": materials,
            "refresh_hours": REFRESH_HOURS,
            "stats": stats,
            "active_tab": "cs2",
        }
    )




@router.get("/items/{item_id}")
def item_detail(request: Request, item_id: int, db: Session = Depends(get_db)):
    item = db.query(TrackedItem).filter(TrackedItem.id == item_id).first()
    if not item:
        return RedirectResponse("/", status_code=302)

    records = (
        db.query(PriceHistory)
        .filter(PriceHistory.tracked_item_id == item_id)
        .order_by(PriceHistory.collected_at.asc())
        .limit(500)
        .all()
    )

    prices = [r.price for r in records if r.price is not None]
    medians = [r.median_price for r in records if r.median_price is not None]
    volumes = [r.volume for r in records if r.volume is not None]

    price_stats = {
        "min": min(prices) if prices else None,
        "max": max(prices) if prices else None,
        "avg": round(sum(prices) / len(prices), 2) if prices else None,
        "latest": prices[-1] if prices else None,
        "median_latest": medians[-1] if medians else None,
        "total_vol": sum(volumes) if volumes else None,
        "count": len(records),
    }

    chart_labels = [r.collected_at.strftime("%d/%m %H:%M") for r in records]
    chart_prices = [r.price for r in records]
    chart_medians = [r.median_price for r in records]

    active_tab = "tbh" if item.appid == TBH_APPID else "cs2"
    icon_url = get_item_icon_url(item.market_hash_name, item.appid)
    is_tbh_app = item.appid == TBH_APPID
    db_item = get_item_by_market_name(item.market_hash_name) if is_tbh_app else None
    grade = db_item.get("grade", "") if db_item else ""
    grade_color = get_grade_color(grade) if grade else ""
    return templates.TemplateResponse(
        "item_detail.html",
        {
            "request": request,
            "item": item,
            "records": records,
            "price_stats": price_stats,
            "chart_labels": chart_labels,
            "chart_prices": chart_prices,
            "chart_medians": chart_medians,
            "active_tab": active_tab,
            "icon_url": icon_url,
            "grade": grade,
            "grade_color": grade_color,
            "is_tbh_app": is_tbh_app,
        },
    )
