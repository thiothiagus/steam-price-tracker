import asyncio
import logging
import time
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

STEAM_PRICE_OVERVIEW_URL = "https://steamcommunity.com/market/priceoverview/"


class SteamCollector:
    def __init__(self) -> None:
        self._client: httpx.AsyncClient | None = None
        self._currency = settings.STEAM_CURRENCY
        self._delay = settings.COLLECTOR_DELAY_SECONDS
        self._max_retries = settings.COLLECTOR_MAX_RETRIES
        self._backoff_factor = settings.COLLECTOR_BACKOFF_FACTOR
        self._rate_limited_until: float = 0.0

    @property
    def rate_limited_until(self) -> float:
        return self._rate_limited_until

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=30.0,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    ),
                    "Accept-Language": "en-US,en;q=0.9",
                },
            )
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def fetch_price(self, appid: int, market_hash_name: str) -> dict[str, Any]:
        client = await self._get_client()
        params = {
            "appid": appid,
            "currency": self._currency,
            "market_hash_name": market_hash_name,
        }

        if self._rate_limited_until > time.time():
            wait = self._rate_limited_until - time.time()
            logger.info(
                "Aguardando rate limit: %.1fs antes de consultar %s",
                wait, market_hash_name,
            )
            await asyncio.sleep(wait)

        for attempt in range(1, self._max_retries + 1):
            try:
                response = await client.get(STEAM_PRICE_OVERVIEW_URL, params=params)
                response.raise_for_status()
                data = response.json()

                if not data.get("success", False):
                    logger.warning(
                        "Steam returned success=false for %s (appid=%s)",
                        market_hash_name, appid,
                    )
                    return {"success": False}

                return self._parse_response(data)

            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code
                if status == 429:
                    wait = (self._backoff_factor ** attempt) * 5
                    self._rate_limited_until = time.time() + wait + 30
                    logger.warning(
                        "Rate limited (429) para %s — aguardando %.1fs "
                        "(global cooldown até %ds)",
                        market_hash_name, wait, int(self._rate_limited_until - time.time()),
                    )
                else:
                    wait = self._backoff_factor ** attempt
                    logger.warning(
                        "HTTP %s for %s (attempt %s/%s, wait %.1fs)",
                        status, market_hash_name, attempt, self._max_retries, wait,
                    )
                if attempt < self._max_retries:
                    await asyncio.sleep(wait)
                else:
                    logger.error(
                        "Max retries reached for %s (appid=%s)",
                        market_hash_name, appid,
                    )
                    return {"success": False, "error": str(exc)}

            except httpx.RequestError as exc:
                logger.error("Request error for %s: %s", market_hash_name, exc)
                return {"success": False, "error": str(exc)}

            finally:
                if attempt < self._max_retries:
                    await asyncio.sleep(self._delay)

        return {"success": False}

    @staticmethod
    def _parse_response(data: dict[str, Any]) -> dict[str, Any]:
        lowest_price = data.get("lowest_price")
        median_price = data.get("median_price")
        volume = data.get("volume")

        def parse_price(value: str | None) -> float | None:
            if value is None:
                return None
            try:
                cleaned = value.replace("R$ ", "").replace("$ ", "").replace(",", ".").strip()
                return float(cleaned)
            except (ValueError, AttributeError):
                return None

        return {
            "success": True,
            "lowest_price": parse_price(lowest_price),
            "median_price": parse_price(median_price),
            "volume": int(volume.replace(",", "")) if volume else None,
        }


collector = SteamCollector()
