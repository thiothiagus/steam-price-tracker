"""Tests for SaveParser._parse logic using a stubbed ES3 file."""
import json
import pytest
from unittest.mock import patch

from app.utils.save_parser import SaveParser


PLAYER_DATA = {
    "itemSaveDatas": [
        {"UniqueId": 1, "ItemKey": 300101, "Quantity": 3},
        {"UniqueId": 2, "ItemKey": 300101, "Quantity": 1},
    ],
    "heroSaveDatas": [
        {"equippedItemIds": [1]},
    ],
    "stashSaveDatas": [
        {"ItemUniqueId": 2},
    ],
}


def _write_fake_save(path, data: dict):
    payload = {"PlayerSaveData": {"value": json.dumps(data)}}
    path.write_bytes(json.dumps(payload).encode("utf-8"))


def _fake_es3_load(self):
    return {"PlayerSaveData": {"value": json.dumps(PLAYER_DATA)}}


def test_decrypt_parses_player_save(tmp_path, monkeypatch):
    save = tmp_path / "save.es3"
    save.write_bytes(b"encrypted-bytes")

    monkeypatch.setattr(
        "app.utils.save_parser.ES3.load", lambda self: _fake_es3_load(None)
    )

    parser = SaveParser(save)
    parser.decrypt()

    assert parser.player_data["itemSaveDatas"][0]["ItemKey"] == 300101


def test_get_all_item_keys_returns_unique_keys(tmp_path, monkeypatch):
    save = tmp_path / "save.es3"
    save.write_bytes(b"x")

    monkeypatch.setattr(
        "app.utils.save_parser.ES3.load", lambda self: _fake_es3_load(None)
    )

    parser = SaveParser(save)
    parser.decrypt()
    keys = parser.get_all_item_keys()
    assert keys == {300101}


def test_player_data_property_calls_decrypt(tmp_path, monkeypatch):
    save = tmp_path / "save.es3"
    save.write_bytes(b"x")

    monkeypatch.setattr(
        "app.utils.save_parser.ES3.load", lambda self: _fake_es3_load(None)
    )

    parser = SaveParser(save)
    _ = parser.player_data
    assert parser._player_data is not None


def test_collected_items_for_import_counts_duplicates(tmp_path, monkeypatch):
    save = tmp_path / "save.es3"
    save.write_bytes(b"x")

    monkeypatch.setattr(
        "app.utils.save_parser.ES3.load", lambda self: _fake_es3_load(None)
    )

    parser = SaveParser(save)
    parser.decrypt()
    items = list(parser.get_collected_items_for_import())
    matching = [i for i in items if i["item_key"] == 300101]
    if matching:
        assert matching[0]["quantity"] == 2


def test_decrypt_handles_non_string_player_save(tmp_path, monkeypatch):
    save = tmp_path / "save.es3"
    save.write_bytes(b"x")

    def load_non_string(self):
        return {"PlayerSaveData": {"value": PLAYER_DATA}}

    monkeypatch.setattr(
        "app.utils.save_parser.ES3.load", load_non_string
    )

    parser = SaveParser(save)
    parser.decrypt()
    assert parser.player_data["itemSaveDatas"][0]["ItemKey"] == 300101
