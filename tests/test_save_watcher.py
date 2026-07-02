"""Tests for SaveWatcher: file detection, copy, polling lifecycle."""
import os
import time
from pathlib import Path

import pytest

from app.services.save_watcher import SaveWatcher


def _write(path: Path, content: bytes = b"savedata") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def test_watcher_starts_and_stops(tmp_path: Path):
    src = tmp_path / "src" / "save.es3"
    dest = tmp_path / "dest" / "save.es3"
    _write(src)

    watcher = SaveWatcher(
        source_path=src,
        dest_path=dest,
        cooldown_seconds=0.0,
        poll_interval=0.05,
    )
    watcher.start()
    try:
        time.sleep(0.2)
        assert watcher.is_running
    finally:
        watcher.stop()
    assert not watcher.is_running


def test_watcher_copies_modified_file(tmp_path: Path):
    src = tmp_path / "src" / "save.es3"
    dest = tmp_path / "dest" / "save.es3"
    _write(src, b"v1")

    watcher = SaveWatcher(
        source_path=src,
        dest_path=dest,
        cooldown_seconds=0.0,
        poll_interval=0.05,
    )
    watcher.start()
    try:
        time.sleep(0.15)
        assert dest.exists()
        assert dest.read_bytes() == b"v1"
    finally:
        watcher.stop()


def test_watcher_reports_missing_source(tmp_path: Path):
    src = tmp_path / "missing.es3"
    dest = tmp_path / "dest" / "save.es3"

    watcher = SaveWatcher(
        source_path=src,
        dest_path=dest,
        cooldown_seconds=0.0,
        poll_interval=0.05,
    )
    assert not watcher.source_exists
    watcher.start()
    try:
        time.sleep(0.15)
        assert watcher.error is not None
        assert "não encontrado" in watcher.error.lower() or "not found" in watcher.error.lower()
    finally:
        watcher.stop()


def test_watcher_does_not_start_twice(tmp_path: Path):
    src = tmp_path / "src" / "save.es3"
    dest = tmp_path / "dest" / "save.es3"
    _write(src)

    watcher = SaveWatcher(
        source_path=src,
        dest_path=dest,
        cooldown_seconds=0.0,
        poll_interval=0.05,
    )
    watcher.start()
    try:
        second_thread = watcher._thread
        watcher.start()
        assert watcher._thread is second_thread
    finally:
        watcher.stop()


def test_watcher_stop_is_idempotent(tmp_path: Path):
    src = tmp_path / "src" / "save.es3"
    dest = tmp_path / "dest" / "save.es3"
    _write(src)

    watcher = SaveWatcher(
        source_path=src,
        dest_path=dest,
        cooldown_seconds=0.0,
        poll_interval=0.05,
    )
    watcher.stop()
    stop_thread = watcher._thread
    watcher.stop()
    assert watcher._thread is stop_thread
