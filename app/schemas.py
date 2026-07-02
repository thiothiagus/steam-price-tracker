from datetime import datetime
from pydantic import BaseModel


class TrackedItemCreate(BaseModel):
    appid: int
    market_hash_name: str
    enabled: bool = True


class TrackedItemResponse(BaseModel):
    id: int
    appid: int
    market_hash_name: str
    enabled: bool
    removed_at: datetime | None = None

    class Config:
        from_attributes = True


class PriceHistoryResponse(BaseModel):
    id: int
    tracked_item_id: int
    price: float | None
    median_price: float | None
    volume: int | None
    collected_at: str

    class Config:
        from_attributes = True


class PriceCollectResponse(BaseModel):
    success: bool
    lowest_price: float | None = None
    median_price: float | None = None
    volume: int | None = None
    error: str | None = None
