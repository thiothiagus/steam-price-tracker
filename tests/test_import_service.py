"""Tests for import_service.import_from_save against a real in-memory SQLite DB."""
from datetime import datetime, timezone
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.db import Base
from app.models.models import TrackedItem
from app.services import import_service


def _fake_save_items() -> list[dict]:
    return [
        {
            "appid": 3678970,
            "market_hash_name": "Bronze Ingot",
            "item_key": 100001,
            "name": "Bronze Ingot",
            "grade": "COMMON",
            "type": "MATERIAL",
            "quantity": 5,
            "is_equipped": False,
            "is_in_stash": False,
        },
        {
            "appid": 3678970,
            "market_hash_name": "Iron Ingot",
            "item_key": 100002,
            "name": "Iron Ingot",
            "grade": "COMMON",
            "type": "MATERIAL",
            "quantity": 3,
            "is_equipped": False,
            "is_in_stash": True,
        },
    ]


@pytest.fixture
def fake_session_factory():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=engine
    )

    def factory():
        return SessionLocal()

    yield factory
    Base.metadata.drop_all(bind=engine)


def test_import_creates_new_tracked_items(
    monkeypatch: pytest.MonkeyPatch, fake_session_factory
):
    monkeypatch.setattr(
        import_service.SaveParser,
        "get_collected_items_for_import",
        lambda self: iter(_fake_save_items()),
    )
    monkeypatch.setattr(import_service, "SessionLocal", fake_session_factory)

    result = import_service.import_from_save(Path("dummy.es3"))

    assert result["imported"] == 2
    assert result["total_found"] == 2
    assert len(result["items"]) == 2


def test_import_returns_message_when_empty(
    monkeypatch: pytest.MonkeyPatch, fake_session_factory
):
    monkeypatch.setattr(
        import_service.SaveParser,
        "get_collected_items_for_import",
        lambda self: iter([]),
    )
    monkeypatch.setattr(import_service, "SessionLocal", fake_session_factory)

    result = import_service.import_from_save(Path("dummy.es3"))

    assert result["imported"] == 0
    assert "Nenhum item" in result["message"]


def test_import_skips_and_updates_existing(
    monkeypatch: pytest.MonkeyPatch, fake_session_factory
):
    """If a tracked_item exists with the same key but different quantity,
    the import updates it rather than creating a duplicate."""
    db = fake_session_factory()
    db.add(
        TrackedItem(
            appid=3678970,
            market_hash_name="Bronze Ingot",
            quantity=2,
            enabled=True,
        )
    )
    db.commit()
    db.close()

    monkeypatch.setattr(
        import_service.SaveParser,
        "get_collected_items_for_import",
        lambda self: iter(_fake_save_items()),
    )
    monkeypatch.setattr(import_service, "SessionLocal", fake_session_factory)

    result = import_service.import_from_save(Path("dummy.es3"))

    assert result["imported"] == 1
    assert result["updated"] >= 1

    verify_db = fake_session_factory()
    bronze = (
        verify_db.query(TrackedItem)
        .filter(TrackedItem.market_hash_name == "Bronze Ingot")
        .all()
    )
    assert len(bronze) == 1
    assert bronze[0].quantity == 5
    verify_db.close()


def test_import_soft_deletes_removed_items(
    monkeypatch: pytest.MonkeyPatch, fake_session_factory
):
    db = fake_session_factory()
    orphan = TrackedItem(
        appid=3678970,
        market_hash_name="Phantom Gem",
        quantity=1,
        enabled=True,
    )
    db.add(orphan)
    db.commit()
    orphan_id = orphan.id
    db.close()

    monkeypatch.setattr(
        import_service.SaveParser,
        "get_collected_items_for_import",
        lambda self: iter(_fake_save_items()[:1]),
    )
    monkeypatch.setattr(import_service, "SessionLocal", fake_session_factory)

    result = import_service.import_from_save(Path("dummy.es3"))

    assert result["removed"] >= 1

    verify_db = fake_session_factory()
    refreshed = (
        verify_db.query(TrackedItem)
        .filter(TrackedItem.id == orphan_id)
        .first()
    )
    assert refreshed is not None
    assert refreshed.removed_at is not None
    verify_db.close()


def test_import_reactivates_archived_items(
    monkeypatch: pytest.MonkeyPatch, fake_session_factory
):
    db = fake_session_factory()
    archived_time = datetime(2020, 1, 1, tzinfo=timezone.utc)
    db.add(
        TrackedItem(
            appid=3678970,
            market_hash_name="Bronze Ingot",
            quantity=5,
            enabled=True,
            removed_at=archived_time,
        )
    )
    db.commit()
    db.close()

    monkeypatch.setattr(
        import_service.SaveParser,
        "get_collected_items_for_import",
        lambda self: iter(_fake_save_items()[:1]),
    )
    monkeypatch.setattr(import_service, "SessionLocal", fake_session_factory)

    result = import_service.import_from_save(Path("dummy.es3"))

    assert result["reactivated"] >= 1

    verify_db = fake_session_factory()
    reactivated = (
        verify_db.query(TrackedItem)
        .filter(TrackedItem.market_hash_name == "Bronze Ingot")
        .first()
    )
    assert reactivated.removed_at is None
    verify_db.close()
