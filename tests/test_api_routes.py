"""
Tests for API routes.
"""
import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from sqlalchemy.orm import Session

from app.api.routes import router
from app.database.db import get_db


@pytest.fixture
def app():
    """Create a FastAPI app for testing."""
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def client(app, db_override):
    """Create a test client with database override."""
    app.dependency_overrides[get_db] = db_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


class TestItemEndpoints:
    """Test item-related API endpoints."""

    def test_list_items_empty(self, client: TestClient):
        """Test listing items when database is empty."""
        response = client.get("/api/items")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_items_with_data(self, client: TestClient, sample_tracked_item):
        """Test listing items with data in database."""
        response = client.get("/api/items")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["appid"] == 730
        assert "AK-47" in data[0]["market_hash_name"]

    def test_create_item_success(self, client: TestClient):
        """Test creating a new item."""
        payload = {
            "appid": 730,
            "market_hash_name": "AWP | Asiimov (Field-Tested)",
            "enabled": True,
        }
        response = client.post("/api/items", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["appid"] == 730
        assert "AWP" in data["market_hash_name"]

    def test_create_item_duplicate(self, client: TestClient, sample_tracked_item):
        """Test creating a duplicate item."""
        payload = {
            "appid": 730,
            "market_hash_name": "AK-47 | Redline (Field-Tested)",
            "enabled": True,
        }
        response = client.post("/api/items", json=payload)
        assert response.status_code == 409
        assert "already tracked" in response.json()["detail"].lower()

    def test_delete_item_success(self, client: TestClient, sample_tracked_item):
        """Test deleting an item."""
        response = client.delete(f"/api/items/{sample_tracked_item.id}")
        assert response.status_code == 204

    def test_delete_item_not_found(self, client: TestClient):
        """Test deleting a non-existent item."""
        response = client.delete("/api/items/99999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_toggle_item(self, client: TestClient, sample_tracked_item):
        """Test toggling item enabled status."""
        assert sample_tracked_item.enabled is True
        
        response = client.patch(f"/api/items/{sample_tracked_item.id}/toggle")
        assert response.status_code == 200
        data = response.json()
        assert data["enabled"] is False
        
        response = client.patch(f"/api/items/{sample_tracked_item.id}/toggle")
        assert response.status_code == 200
        data = response.json()
        assert data["enabled"] is True

    def test_toggle_item_not_found(self, client: TestClient):
        """Test toggling a non-existent item."""
        response = client.patch("/api/items/99999/toggle")
        assert response.status_code == 404


class TestPriceHistoryEndpoints:
    """Test price history endpoints."""

    def test_get_price_history(self, client: TestClient, sample_tracked_item, sample_price_history):
        """Test getting price history for an item."""
        response = client.get(f"/api/items/{sample_tracked_item.id}/history")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_get_price_history_with_limit(self, client: TestClient, sample_tracked_item, sample_price_history):
        """Test getting price history with limit parameter."""
        response = client.get(f"/api/items/{sample_tracked_item.id}/history?limit=1")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

    def test_get_price_history_item_not_found(self, client: TestClient):
        """Test getting history for non-existent item."""
        response = client.get("/api/items/99999/history")
        assert response.status_code == 404


class TestCollectionEndpoints:
    """Test collection-related endpoints."""

    @pytest.mark.asyncio
    def test_collect_item_price(self, client: TestClient, sample_tracked_item, monkeypatch):
        """Test triggering price collection for a single item."""
        mock_collect = AsyncMock(return_value={
            "success": True,
            "lowest_price": 150.0,
            "median_price": 155.0,
            "volume": "100",
        })
        monkeypatch.setattr("app.api.routes.collect_single_item", mock_collect)
        
        response = client.post(f"/api/items/{sample_tracked_item.id}/collect")
        assert response.status_code == 200

    @pytest.mark.asyncio
    def test_collect_all_prices(self, client: TestClient, monkeypatch):
        """Test triggering full price collection."""
        mock_collect = AsyncMock(return_value={
            "success": True,
            "message": "Collection completed",
            "collected": 5,
            "total": 5,
        })
        monkeypatch.setattr("app.api.routes.collect_all_prices", mock_collect)
        
        response = client.post("/api/collect")
        assert response.status_code == 200

    def test_collection_cooldown(self, client: TestClient):
        """Test getting collection cooldown status."""
        response = client.get("/api/collect/cooldown")
        assert response.status_code == 200
        data = response.json()
        assert "rate_limited" in data
        assert "cooldown_remaining" in data


class TestSaveWatcherEndpoints:
    """Test save watcher endpoints."""

    def test_watcher_status(self, client: TestClient, monkeypatch):
        """Test getting watcher status."""
        mock_watcher = MagicMock()
        mock_watcher.is_running = True
        mock_watcher.source_exists = True
        mock_watcher.source_path = "/fake/source"
        mock_watcher.dest_path = "/fake/dest"
        mock_watcher.error = None
        
        monkeypatch.setattr("app.state.save_watcher", mock_watcher)
        
        response = client.get("/api/watcher/status")
        assert response.status_code == 200
        data = response.json()
        assert data["running"] is True
        assert data["source_exists"] is True

    def test_import_preview(self, client: TestClient, monkeypatch, tmp_path):
        """Test import preview endpoint."""
        save_file = tmp_path / "SaveFile_Live.es3"
        save_file.write_text("fake save content")
        
        monkeypatch.setattr("app.config.settings.BASE_DIR", tmp_path)
        
        mock_parser = MagicMock()
        mock_parser.get_collected_items_for_import.return_value = [
            {"appid": 730, "market_hash_name": "Test Item", "quantity": 5}
        ]
        monkeypatch.setattr("app.api.routes.SaveParser", lambda x: mock_parser)
        
        response = client.get("/api/import-preview")
        assert response.status_code == 200
        data = response.json()
        assert "total_tradable_items" in data
        assert "items" in data