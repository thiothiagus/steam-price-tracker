import re
import time
import os
from pathlib import Path
from threading import Lock
from typing import Any

import httpx

STEAM_ICON_BASE = "https://community.steamstatic.com/economy/image/"

_cache: dict[str, tuple[float, str | None]] = {}
_cache_lock = Lock()
_CACHE_TTL_SECONDS = 600
_LOCAL_ICONS_DIR = Path(__file__).resolve().parent.parent.parent / "frontend" / "static" / "icons"
_FAILED_CACHE: dict[str, float] = {}
_FAILED_LOCK = Lock()
_FAILED_TTL_SECONDS = 3600


def _make_cache_key(appid: int, market_hash_name: str) -> str:
    return f"{appid}:{market_hash_name}"


def fetch_steam_item_icon(appid: int, market_hash_name: str) -> str | None:
    cache_key = _make_cache_key(appid, market_hash_name)

    with _cache_lock:
        if cache_key in _cache:
            cached_time, cached_url = _cache[cache_key]
            if time.time() - cached_time < _CACHE_TTL_SECONDS:
                return cached_url

    with _FAILED_LOCK:
        if cache_key in _FAILED_CACHE:
            failed_time = _FAILED_CACHE[cache_key]
            if time.time() - failed_time < _FAILED_TTL_SECONDS:
                return None

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    }

    safe_name = market_hash_name.replace("/", "_")
    local_icon_path = _LOCAL_ICONS_DIR / f"{safe_name}.png"

    if local_icon_path.exists():
        return f"/static/icons/{safe_name}.png"

    try:
        market_name = market_hash_name.replace(" ", "%20").replace("&", "%26")
        url = f"https://steamcommunity.com/market/listings/{appid}/{market_name}"

        with httpx.Client(timeout=15.0, follow_redirects=True) as client:
            response = client.get(url, headers=headers)
            response.raise_for_status()
            text = response.text

            matches = re.findall(r"https://community\.steamstatic\.com/economy/image/([^\s\"\'\\]+)", text)
            if matches:
                icon_url = STEAM_ICON_BASE + matches[0]
                with _cache_lock:
                    _cache[cache_key] = (time.time(), icon_url)
                return icon_url

    except Exception:
        pass

    with _FAILED_LOCK:
        _FAILED_CACHE[cache_key] = time.time()

    with _cache_lock:
        _cache[cache_key] = (time.time(), None)

    return None


def fetch_and_save_icon(appid: int, market_hash_name: str) -> str | None:
    icon_url = fetch_steam_item_icon(appid, market_hash_name)
    if not icon_url:
        return None

    safe_name = market_hash_name.replace("/", "_")
    local_icon_path = _LOCAL_ICONS_DIR / f"{safe_name}.png"

    if local_icon_path.exists():
        return f"/static/icons/{safe_name}.png"

    try:
        with httpx.Client(timeout=20.0) as client:
            response = client.get(icon_url, headers={"User-Agent": "Mozilla/5.0"})
            if response.status_code == 200 and len(response.content) > 1000:
                with open(local_icon_path, "wb") as f:
                    f.write(response.content)

                app_icons_dir = Path(__file__).resolve().parent.parent / "data" / "icons"
                app_icons_dir.mkdir(parents=True, exist_ok=True)
                app_copy = app_icons_dir / f"{safe_name}.png"
                with open(app_copy, "wb") as f:
                    f.write(response.content)

                return f"/static/icons/{safe_name}.png"
    except Exception:
        pass

    return icon_url


def clear_icon_cache() -> None:
    with _cache_lock:
        _cache.clear()
    with _FAILED_LOCK:
        _FAILED_CACHE.clear()