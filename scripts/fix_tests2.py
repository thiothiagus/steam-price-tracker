with open('tests/test_collector_service.py', 'r') as f:
    content = f.read()

# Fix test_collect_all_prices_steam_failure
old1 = '''    async def test_collect_all_prices_steam_failure(self, test_db_session: Session, sample_tracked_item, monkeypatch):
        """Test collection when Steam API fails."""
        monkeypatch.setattr("app.services.collector_service.SessionLocal", lambda: test_db_session)
        
        mock_fetch = AsyncMock(return_value={"success": False})
        monkeypatch.setattr(collector, "fetch_price", mock_fetch)
        
        result = await collect_all_prices(force=True)
        
        assert result["success"] is True
        assert result["collected"] == 0
        
        records = test_db_session.query(PriceHistory).filter(
            PriceHistory.tracked_item_id == sample_tracked_item.id
        ).all()
        assert len(records) == 0'''

new1 = '''    async def test_collect_all_prices_steam_failure(self, collector_session_factory, sample_tracked_item, monkeypatch):
        """Test collection when Steam API fails."""
        monkeypatch.setattr("app.services.collector_service.SessionLocal", collector_session_factory)
        
        mock_fetch = AsyncMock(return_value={"success": False})
        monkeypatch.setattr(collector, "fetch_price", mock_fetch)
        
        result = await collect_all_prices(force=True)
        
        assert result["success"] is True
        assert result["collected"] == 0
        
        # Verify no price history was created using a new session
        session = collector_session_factory()
        try:
            records = session.query(PriceHistory).filter(
                PriceHistory.tracked_item_id == sample_tracked_item.id
            ).all()
            assert len(records) == 0
        finally:
            session.close()'''

# Fix test_collect_all_prices_rate_limit
old2 = '''    async def test_collect_all_prices_rate_limit(self, test_db_session: Session, sample_tracked_item, monkeypatch):
        """Test collection when rate limited."""
        monkeypatch.setattr("app.services.collector_service.SessionLocal", lambda: test_db_session)
        monkeypatch.setattr(collector, "rate_limited_until", 9999999999)
        
        result = await collect_all_prices(force=True)
        
        assert result["success"] is False
        assert "Rate limit" in result.get("message", "")
        assert "cooldown_remaining" in result'''

new2 = '''    async def test_collect_all_prices_rate_limit(self, collector_session_factory, sample_tracked_item, monkeypatch):
        """Test collection when rate limited."""
        monkeypatch.setattr("app.services.collector_service.SessionLocal", collector_session_factory)
        # Use the internal attribute since rate_limited_until is a property
        monkeypatch.setattr(collector, "_rate_limited_until", 9999999999)
        
        result = await collect_all_prices(force=True)
        
        assert result["success"] is False
        assert "Rate limit" in result.get("message", "")
        assert "cooldown_remaining" in result'''

# Fix test_collect_all_prices_respects_refresh_hours
old3 = '''    async def test_collect_all_prices_respects_refresh_hours(self, test_db_session: Session, sample_tracked_item, monkeypatch):
        """Test that collection respects refresh hours setting."""
        monkeypatch.setattr("app.services.collector_service.SessionLocal", lambda: test_db_session)
        monkeypatch.setattr("app.services.collector_service.REFRESH_HOURS", 1)
        
        recent_record = PriceHistory(
            tracked_item_id=sample_tracked_item.id,
            price=100.0,
            median_price=105.0,
            volume=50,
            collected_at=datetime.now(timezone.utc) - timedelta(minutes=30),
        )
        test_db_session.add(recent_record)
        test_db_session.commit()
        
        result = await collect_all_prices(force=False)
        
        assert result["success"] is True
        assert result["collected"] == 0
        assert "atualizados" in result.get("message", "")'''

new3 = '''    async def test_collect_all_prices_respects_refresh_hours(self, collector_session_factory, sample_tracked_item, monkeypatch):
        """Test that collection respects refresh hours setting."""
        monkeypatch.setattr("app.services.collector_service.SessionLocal", collector_session_factory)
        monkeypatch.setattr("app.services.collector_service.REFRESH_HOURS", 1)
        
        session = collector_session_factory()
        try:
            recent_record = PriceHistory(
                tracked_item_id=sample_tracked_item.id,
                price=100.0,
                median_price=105.0,
                volume=50,
                collected_at=datetime.now(timezone.utc) - timedelta(minutes=30),
            )
            session.add(recent_record)
            session.commit()
        finally:
            session.close()
        
        result = await collect_all_prices(force=False)
        
        assert result["success"] is True
        assert result["collected"] == 0
        assert "atualizados" in result.get("message", "")'''

# Fix test_collect_all_prices_force_ignores_refresh_hours
old4 = '''    async def test_collect_all_prices_force_ignores_refresh_hours(self, test_db_session: Session, sample_tracked_item, monkeypatch):
        """Test that force=True ignores refresh hours."""
        monkeypatch.setattr("app.services.collector_service.SessionLocal", lambda: test_db_session)
        monkeypatch.setattr("app.services.collector_service.REFRESH_HOURS", 1)
        
        recent_record = PriceHistory(
            tracked_item_id=sample_tracked_item.id,
            price=100.0,
            median_price=105.0,
            volume=50,
            collected_at=datetime.now(timezone.utc) - timedelta(minutes=30),
        )
        test_db_session.add(recent_record)
        test_db_session.commit()
        
        mock_fetch = AsyncMock(return_value={
            "success": True,
            "lowest_price": 150.0,
            "median_price": 155.0,
            "volume": 100,
        })
        monkeypatch.setattr(collector, "fetch_price", mock_fetch)
        
        result = await collect_all_prices(force=True)
        
        assert result["success"] is True
        assert result["collected"] == 1'''

new4 = '''    async def test_collect_all_prices_force_ignores_refresh_hours(self, collector_session_factory, sample_tracked_item, monkeypatch):
        """Test that force=True ignores refresh hours."""
        monkeypatch.setattr("app.services.collector_service.SessionLocal", collector_session_factory)
        monkeypatch.setattr("app.services.collector_service.REFRESH_HOURS", 1)
        
        session = collector_session_factory()
        try:
            recent_record = PriceHistory(
                tracked_item_id=sample_tracked_item.id,
                price=100.0,
                median_price=105.0,
                volume=50,
                collected_at=datetime.now(timezone.utc) - timedelta(minutes=30),
            )
            session.add(recent_record)
            session.commit()
        finally:
            session.close()
        
        mock_fetch = AsyncMock(return_value={
            "success": True,
            "lowest_price": 150.0,
            "median_price": 155.0,
            "volume": 100,
        })
        monkeypatch.setattr(collector, "fetch_price", mock_fetch)
        
        result = await collect_all_prices(force=True)
        
        assert result["success"] is True
        assert result["collected"] == 1'''

# Fix test_collect_single_item_success
old5 = '''    async def test_collect_single_item_success(self, test_db_session: Session, sample_tracked_item, monkeypatch):
        """Test successful single item collection."""
        monkeypatch.setattr("app.services.collector_service.SessionLocal", lambda: test_db_session)
        
        mock_fetch = AsyncMock(return_value={
            "success": True,
            "lowest_price": 175.0,
            "median_price": 180.0,
            "volume": 200,
        })
        monkeypatch.setattr(collector, "fetch_price", mock_fetch)
        
        result = await collect_single_item(sample_tracked_item.id)
        
        assert result is not None
        assert result["success"] is True
        assert result["lowest_price"] == 175.0
        
        records = test_db_session.query(PriceHistory).filter(
            PriceHistory.tracked_item_id == sample_tracked_item.id
        ).all()
        assert len(records) == 1
        assert records[0].price == 175.0'''

new5 = '''    async def test_collect_single_item_success(self, collector_session_factory, sample_tracked_item, monkeypatch):
        """Test successful single item collection."""
        monkeypatch.setattr("app.services.collector_service.SessionLocal", collector_session_factory)
        
        mock_fetch = AsyncMock(return_value={
            "success": True,
            "lowest_price": 175.0,
            "median_price": 180.0,
            "volume": 200,
        })
        monkeypatch.setattr(collector, "fetch_price", mock_fetch)
        
        result = await collect_single_item(sample_tracked_item.id)
        
        assert result is not None
        assert result["success"] is True
        assert result["lowest_price"] == 175.0
        
        # Verify price history was created using a new session
        session = collector_session_factory()
        try:
            records = session.query(PriceHistory).filter(
                PriceHistory.tracked_item_id == sample_tracked_item.id
            ).all()
            assert len(records) == 1
            assert records[0].price == 175.0
        finally:
            session.close()'''

# Fix test_collect_single_item_not_found
old6 = '''    async def test_collect_single_item_not_found(self, test_db_session: Session, monkeypatch):
        """Test collection for non-existent item."""
        monkeypatch.setattr("app.services.collector_service.SessionLocal", lambda: test_db_session)
        
        result = await collect_single_item(99999)
        
        assert result is None'''

new6 = '''    async def test_collect_single_item_not_found(self, collector_session_factory, monkeypatch):
        """Test collection for non-existent item."""
        monkeypatch.setattr("app.services.collector_service.SessionLocal", collector_session_factory)
        
        result = await collect_single_item(99999)
        
        assert result is None'''

# Fix test_collect_single_item_steam_failure
old7 = '''    async def test_collect_single_item_steam_failure(self, test_db_session: Session, sample_tracked_item, monkeypatch):
        """Test collection when Steam API fails."""
        monkeypatch.setattr("app.services.collector_service.SessionLocal", lambda: test_db_session)
        
        mock_fetch = AsyncMock(return_value={"success": False})
        monkeypatch.setattr(collector, "fetch_price", mock_fetch)
        
        result = await collect_single_item(sample_tracked_item.id)
        
        assert result is not None
        assert result["success"] is False
        
        records = test_db_session.query(PriceHistory).filter(
            PriceHistory.tracked_item_id == sample_tracked_item.id
        ).all()
        assert len(records) == 0'''

new7 = '''    async def test_collect_single_item_steam_failure(self, collector_session_factory, sample_tracked_item, monkeypatch):
        """Test collection when Steam API fails."""
        monkeypatch.setattr("app.services.collector_service.SessionLocal", collector_session_factory)
        
        mock_fetch = AsyncMock(return_value={"success": False})
        monkeypatch.setattr(collector, "fetch_price", mock_fetch)
        
        result = await collect_single_item(sample_tracked_item.id)
        
        assert result is not None
        assert result["success"] is False
        
        # Verify no price history was created using a new session
        session = collector_session_factory()
        try:
            records = session.query(PriceHistory).filter(
                PriceHistory.tracked_item_id == sample_tracked_item.id
            ).all()
            assert len(records) == 0
        finally:
            session.close()'''

if old1 in content:
    content = content.replace(old1, new1)
    print('Fixed test_collect_all_prices_steam_failure')
else:
    print('NOT FOUND: test_collect_all_prices_steam_failure')

if old2 in content:
    content = content.replace(old2, new2)
    print('Fixed test_collect_all_prices_rate_limit')
else:
    print('NOT FOUND: test_collect_all_prices_rate_limit')

if old3 in content:
    content = content.replace(old3, new3)
    print('Fixed test_collect_all_prices_respects_refresh_hours')
else:
    print('NOT FOUND: test_collect_all_prices_respects_refresh_hours')

if old4 in content:
    content = content.replace(old4, new4)
    print('Fixed test_collect_all_prices_force_ignores_refresh_hours')
else:
    print('NOT FOUND: test_collect_all_prices_force_ignores_refresh_hours')

if old5 in content:
    content = content.replace(old5, new5)
    print('Fixed test_collect_single_item_success')
else:
    print('NOT FOUND: test_collect_single_item_success')

if old6 in content:
    content = content.replace(old6, new6)
    print('Fixed test_collect_single_item_not_found')
else:
    print('NOT FOUND: test_collect_single_item_not_found')

if old7 in content:
    content = content.replace(old7, new7)
    print('Fixed test_collect_single_item_steam_failure')
else:
    print('NOT FOUND: test_collect_single_item_steam_failure')

with open('tests/test_collector_service.py', 'w') as f:
    f.write(content)

print('Done')