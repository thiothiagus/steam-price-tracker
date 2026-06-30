from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.database.db import Base


class TrackedItem(Base):
    __tablename__ = "tracked_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    appid = Column(Integer, nullable=False, index=True)
    market_hash_name = Column(Text, nullable=False)
    enabled = Column(Boolean, default=True, nullable=False)
    quantity = Column(Integer, default=1, nullable=False)
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    price_records = relationship(
        "PriceHistory", back_populates="tracked_item", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<TrackedItem appid={self.appid} name={self.market_hash_name!r}>"


class PriceHistory(Base):
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tracked_item_id = Column(
        Integer, ForeignKey("tracked_items.id"), nullable=False, index=True
    )
    price = Column(Float, nullable=True)
    median_price = Column(Float, nullable=True)
    volume = Column(Integer, nullable=True)
    collected_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    tracked_item = relationship("TrackedItem", back_populates="price_records")

    def __repr__(self) -> str:
        return f"<PriceHistory item_id={self.tracked_item_id} price={self.price}>"
