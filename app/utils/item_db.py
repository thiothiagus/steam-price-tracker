import json
from pathlib import Path
from typing import Any

from app.config import settings

_ITEM_DB_DIR = Path(__file__).resolve().parent.parent / "data"
_ICONS_DIR = _ITEM_DB_DIR / "icons"
_STEAM_ICON_BASE = "https://community.steamstatic.com/economy/image/"

_ICON_HASHES: dict[str, str | None] | None = None


def _load_icon_hashes() -> dict[str, str | None]:
    global _ICON_HASHES
    if _ICON_HASHES is not None:
        return _ICON_HASHES
    path = _ITEM_DB_DIR / "icon_hashes.json"
    if not path.exists():
        _ICON_HASHES = {}
        return _ICON_HASHES
    with open(path, "r", encoding="utf-8") as f:
        _ICON_HASHES = json.load(f)
    return _ICON_HASHES


def get_item_icon_url(market_hash_name: str) -> str | None:
    """Retorna URL do ícone do item (local ou Steam)."""
    # Tenta encontrar o ícone local primeiro
    safe_name = market_hash_name.replace("/", "_")
    local_icon_path = _ICONS_DIR / f"{safe_name}.png"
    
    if local_icon_path.exists():
        # Retorna URL estática para o ícone local
        return f"/static/icons/{safe_name}.png"
    
    # Fallback para hash da Steam
    hashes = _load_icon_hashes()
    icon_hash = hashes.get(market_hash_name)
    if not icon_hash:
        return None
    return _STEAM_ICON_BASE + icon_hash


_ITEMS_DB: dict[int, dict[str, Any]] | None = None


def _load_items_db() -> dict[int, dict[str, Any]]:
    global _ITEMS_DB
    if _ITEMS_DB is not None:
        return _ITEMS_DB

    path = Path(__file__).resolve().parent.parent / "data" / "items.json"
    with open(path, "r", encoding="utf-8") as f:
        items = json.load(f)

    db = {}
    for item in items:
        db[item["key"]] = item

    _ITEMS_DB = db
    return db


def get_item(item_key: int) -> dict[str, Any] | None:
    db = _load_items_db()
    return db.get(item_key)


def _title_case_grade(grade: str) -> str:
    return grade.title()


def build_market_name(item: dict[str, Any]) -> str | None:
    if not item.get("tradable"):
        return None

    name = item["name"]
    grade = _title_case_grade(item.get("grade", ""))
    variant = item.get("variant", "")
    item_type = item["type"]

    if item_type == "MATERIAL":
        return name

    if item_type in ("GEAR",):
        if variant:
            return f"{name} ({grade}) {variant}"
        return f"{name} ({grade})"

    if item_type == "STAGEBOX":
        return name

    return name


def is_item_tradable(item_key: int) -> bool:
    item = get_item(item_key)
    if not item:
        return False
    return bool(item.get("tradable", False))


def build_market_name(item: dict[str, Any]) -> str | None:
    if not item.get("tradable"):
        return None

    name = item["name"]
    grade = _title_case_grade(item.get("grade", ""))
    variant = item.get("variant", "")
    item_type = item["type"]

    if item_type == "MATERIAL":
        return name

    if item_type in ("GEAR",):
        if variant:
            return f"{name} ({grade}) {variant}"
        return f"{name} ({grade})"

    if item_type == "STAGEBOX":
        return name

    return name


def get_all_tradable_items() -> list[dict[str, Any]]:
    db = _load_items_db()
    return [item for item in db.values() if item.get("tradable")]


_MARKET_NAME_INDEX: dict[str, dict[str, Any]] | None = None


def _build_market_name_index() -> dict[str, dict[str, Any]]:
    global _MARKET_NAME_INDEX
    if _MARKET_NAME_INDEX is not None:
        return _MARKET_NAME_INDEX
    _MARKET_NAME_INDEX = {}
    for item in get_all_tradable_items():
        name = build_market_name(item)
        if name:
            _MARKET_NAME_INDEX[name] = item
    return _MARKET_NAME_INDEX


def get_item_by_market_name(market_hash_name: str) -> dict[str, Any] | None:
    idx = _build_market_name_index()
    return idx.get(market_hash_name)


GRADE_COLORS: dict[str, str] = {
    "COMMON": "#e4e4e4",
    "UNCOMMON": "#54fc0c",
    "RARE": "#2f8bfc",
    "LEGENDARY": "#fc9c0c",
    "IMMORTAL": "#fc2424",
    "ARCANA": "#b40cfc",
    "BEYOND": "#fc246c",
    "CELESTIAL": "#6ccce4",
    "DIVINE": "#fce454",
    "COSMIC": "#fcfcfc",
}


def get_grade_color(grade: str) -> str:
    return GRADE_COLORS.get(grade, "#ffffff")
