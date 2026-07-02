"""Tests for app.utils.item_db search and market-name helpers."""
import pytest

from app.utils import item_db


def test_search_tradable_market_names_finds_match():
    results = item_db.search_tradable_market_names("amber")
    assert isinstance(results, list)
    if results:
        assert all("market_hash_name" in r and "grade" in r and "type" in r for r in results)


def test_search_tradable_market_names_empty_query():
    assert item_db.search_tradable_market_names("") == []
    assert item_db.search_tradable_market_names("   ") == []


def test_search_tradable_market_names_case_insensitive():
    a = item_db.search_tradable_market_names("Iron")
    b = item_db.search_tradable_market_names("iron")
    assert {r["market_hash_name"] for r in a} == {r["market_hash_name"] for r in b}


def test_search_tradable_market_names_respects_limit():
    results = item_db.search_tradable_market_names("a", limit=3)
    assert len(results) <= 3


def test_get_grade_color_known_and_unknown():
    assert item_db.get_grade_color("IMMORTAL") == "#fc2424"
    assert item_db.get_grade_color("LEGENDARY") == "#fc9c0c"
    assert item_db.get_grade_color("UNKNOWN") == "#ffffff"


def test_build_market_name_for_material():
    item = {
        "name": "Bronze Ingot",
        "type": "MATERIAL",
        "tradable": True,
        "grade": "COMMON",
    }
    assert item_db.build_market_name(item) == "Bronze Ingot"


def test_build_market_name_for_gear_with_variant():
    item = {
        "name": "Dimensional Sword",
        "type": "GEAR",
        "tradable": True,
        "grade": "immortal",
        "variant": "A",
    }
    assert item_db.build_market_name(item) == "Dimensional Sword (Immortal) A"


def test_build_market_name_for_gear_without_variant():
    item = {
        "name": "Long Sword",
        "type": "GEAR",
        "tradable": True,
        "grade": "COMMON",
        "variant": "",
    }
    assert item_db.build_market_name(item) == "Long Sword (Common)"


def test_build_market_name_non_tradable_returns_none():
    item = {
        "name": "Common Junk",
        "type": "MATERIAL",
        "tradable": False,
        "grade": "COMMON",
    }
    assert item_db.build_market_name(item) is None


def test_get_item_by_market_name_lookup():
    db_item = item_db.get_item_by_market_name("Bronze Ingot")
    if db_item is not None:
        assert db_item["type"] == "MATERIAL"
