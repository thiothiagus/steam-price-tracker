"""
Tests for Steam Price Tracker collectors.
"""
import pytest
import time
from unittest.mock import AsyncMock, patch, MagicMock

import httpx
from httpx import Response

from app.collectors.steam import SteamCollector, collector


class TestSteamCollectorInit:
    """Test SteamCollector initialization."""

    def test_collector_initialization(self):
        """Test that collector initializes with correct default values."""
        test_collector = SteamCollector()
        
        assert test_collector._delay > 0
        assert test_collector._max_retries >= 1
        assert test_collector._backoff_factor > 0
        assert test_collector._rate_limited_until == 0.0

    def test_rate_limited_until_property(self):
        """Test rate_limited_until property."""
        test_collector = SteamCollector()
        assert test_collector.rate_limited_until == 0.0
        
        test_collector._rate_limited_until = 123.45
        assert test_collector.rate_limited_until == 123.45


class TestSteamCollectorParseResponse:
    """Test SteamCollector response parsing."""

    def test_parse_response_with_all_fields(self):
        """Test parsing response with all price fields."""
        data = {
            "success": True,
            "lowest_price": "R$ 150,00",
            "median_price": "R$ 155,00",
            "volume": "100",
        }
        
        result = SteamCollector._parse_response(data)
        
        assert result["success"] is True
        assert result["lowest_price"] == 150.0
        assert result["median_price"] == 155.0
        assert result["volume"] == 100

    def test_parse_response_with_usd_currency(self):
        """Test parsing response with USD currency format."""
        data = {
            "success": True,
            "lowest_price": "$ 10.50",
            "median_price": "$ 11.00",
            "volume": "50",
        }
        
        result = SteamCollector._parse_response(data)
        
        assert result["success"] is True
        assert result["lowest_price"] == 10.5
        assert result["median_price"] == 11.0

    def test_parse_response_with_none_values(self):
        """Test parsing response with None values."""
        data = {
            "success": True,
            "lowest_price": None,
            "median_price": None,
            "volume": None,
        }
        
        result = SteamCollector._parse_response(data)
        
        assert result["success"] is True
        assert result["lowest_price"] is None
        assert result["median_price"] is None
        assert result["volume"] is None

    def test_parse_response_with_invalid_price(self):
        """Test parsing response with invalid price format."""
        data = {
            "success": True,
            "lowest_price": "invalid",
            "median_price": "also invalid",
            "volume": "100",
        }
        
        result = SteamCollector._parse_response(data)
        
        assert result["success"] is True
        assert result["lowest_price"] is None
        assert result["median_price"] is None
        assert result["volume"] == 100

    def test_parse_response_with_volume_containing_comma(self):
        """Test parsing volume with comma separator."""
        data = {
            "success": True,
            "lowest_price": "R$ 100,00",
            "median_price": "R$ 105,00",
            "volume": "1,234",
        }
        
        result = SteamCollector._parse_response(data)
        
        assert result["success"] is True
        assert result["lowest_price"] == 100.0
        assert result["median_price"] == 105.0
        assert result["volume"] == 1234


def _make_mock_response(json_data=None, status_code=200):
    """Create a mock httpx.Response."""
    mock_resp = MagicMock(spec=httpx.Response)
    mock_resp.status_code = status_code
    mock_resp.json.return_value = json_data or {}
    mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
        message=f"HTTP {status_code}",
        request=MagicMock(),
        response=mock_resp,
    ) if status_code >= 400 else None
    return mock_resp


@pytest.mark.asyncio
class TestSteamCollectorFetchPrice:
    """Test SteamCollector fetch_price method."""

    @pytest.fixture
    def mock_collector(self):
        """Create a collector with minimal delays for testing."""
        test_collector = SteamCollector()
        test_collector._delay = 0.01
        test_collector._max_retries = 2
        test_collector._backoff_factor = 0.1
        return test_collector

    async def test_fetch_price_success(self, mock_collector: SteamCollector):
        """Test successful price fetch."""
        mock_resp = _make_mock_response({
            "success": True,
            "lowest_price": "R$ 150,00",
            "median_price": "R$ 155,00",
            "volume": "100",
        })

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_resp

        with patch.object(mock_collector, "_get_client", return_value=mock_client):
            result = await mock_collector.fetch_price(730, "AK-47 | Redline (Field-Tested)")

        assert result["success"] is True
        assert result["lowest_price"] == 150.0
        assert result["median_price"] == 155.0
        assert result["volume"] == 100

    async def test_fetch_price_steam_returns_failure(self, mock_collector: SteamCollector):
        """Test when Steam API returns success=false."""
        mock_resp = _make_mock_response({"success": False})

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_resp

        with patch.object(mock_collector, "_get_client", return_value=mock_client):
            result = await mock_collector.fetch_price(730, "Test Item")

        assert result["success"] is False
        assert "error" not in result

    async def test_fetch_price_http_error(self, mock_collector: SteamCollector):
        """Test handling of HTTP errors."""
        mock_resp = MagicMock(spec=httpx.Response)
        mock_resp.status_code = 500
        mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            message="HTTP 500",
            request=MagicMock(),
            response=mock_resp,
        )

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_resp

        with patch.object(mock_collector, "_get_client", return_value=mock_client):
            result = await mock_collector.fetch_price(730, "Test Item")

        assert result["success"] is False

    async def test_fetch_price_rate_limit(self, mock_collector: SteamCollector):
        """Test rate limit handling."""
        mock_collector._rate_limited_until = time.time() + 100

        mock_resp = _make_mock_response({
            "success": True,
            "lowest_price": "R$ 100,00",
            "median_price": "R$ 105,00",
            "volume": "50",
        })

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_resp

        with patch.object(mock_collector, "_get_client", return_value=mock_client):
            result = await mock_collector.fetch_price(730, "Test Item")

        assert result["success"] is True
        assert result["lowest_price"] == 100.0

    async def test_fetch_price_request_error(self, mock_collector: SteamCollector):
        """Test handling of request errors."""
        with patch.object(
            mock_collector,
            "_get_client",
            side_effect=httpx.RequestError("Connection error"),
        ):
            result = await mock_collector.fetch_price(730, "Test Item")
            assert result["success"] is False

    async def test_fetch_price_with_retry(self, mock_collector: SteamCollector):
        """Test retry mechanism on transient failure."""
        error_resp = MagicMock(spec=httpx.Response)
        error_resp.status_code = 503
        error_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            message="HTTP 503",
            request=MagicMock(),
            response=error_resp,
        )

        success_resp = _make_mock_response({
            "success": True,
            "lowest_price": "R$ 200,00",
            "median_price": "R$ 205,00",
            "volume": "75",
        })

        mock_client = AsyncMock()
        mock_client.get.side_effect = [error_resp, success_resp]

        with patch.object(mock_collector, "_get_client", return_value=mock_client):
            result = await mock_collector.fetch_price(730, "Test Item")

        assert result["success"] is True
        assert result["lowest_price"] == 200.0
        assert mock_client.get.call_count == 2

    async def test_close_collector(self, mock_collector: SteamCollector):
        """Test closing the collector client."""
        await mock_collector._get_client()
        await mock_collector.close()
        assert mock_collector._client is None or mock_collector._client.is_closed