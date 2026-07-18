from datetime import datetime
from pydantic import BaseModel, ConfigDict


class TrackedItemCreate(BaseModel):
    appid: int
    market_hash_name: str
    enabled: bool = True


class TrackedItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    appid: int
    market_hash_name: str
    enabled: bool
    removed_at: datetime | None = None


class PriceHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tracked_item_id: int
    price: float | None
    median_price: float | None
    volume: int | None
    collected_at: datetime


class PriceCollectResponse(BaseModel):
    success: bool
    lowest_price: float | None = None
    median_price: float | None = None
    volume: int | None = None
    error: str | None = None
