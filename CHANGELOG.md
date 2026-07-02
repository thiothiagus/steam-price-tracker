# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `GET /api/items/archived` - List archived/removed items
- `POST /api/items/{id}/restore` - Restore an archived item

### Fixed
- Items removed from inventory now disappear from dashboard (soft delete)
- Price collector no longer wastes API calls on removed items

## [1.0.0] - 2026-07-02

### Added
- Steam Market price tracking for TBH and CS2 items
- Dashboard with item tables (GEAR and MATERIAL types)
- Price history with Chart.js visualization
- Automatic collection via APScheduler (hourly)
- Save file watcher for auto-import from Task Bar Hero
- Steam API rate limiting (3s delay, 20 req/min max)
- Item icons downloaded and cached locally
- Price statistics (min, max, avg, total volume)
- Revenue calculator with Steam fees (87% for >= R$1, fixed R$0.10 for < R$1)
- REST API endpoints for items, prices, and collection
- SQLite database with SQLAlchemy ORM
- Pytest test suite with coverage