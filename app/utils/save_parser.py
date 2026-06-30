import json
import logging
from pathlib import Path
from typing import Any

from es3_modifier import ES3

from app.utils.item_db import build_market_name, is_item_tradable, get_item

logger = logging.getLogger(__name__)

ES3_PASSWORD = "emuMqG3bLYJ938ZDCfieWJ"
STEAM_APPID_TBH = 3678970


class SaveParser:
    def __init__(self, save_path: str | Path) -> None:
        self._save_path = Path(save_path)
        self._raw_data: dict | None = None
        self._player_data: dict | None = None

    def decrypt(self) -> dict[str, Any]:
        with open(self._save_path, "rb") as f:
            encrypted = f.read()

        es3 = ES3(encrypted, ES3_PASSWORD)
        decrypted = es3.load()

        psd_raw = decrypted.get("PlayerSaveData", {}).get("value", "")
        if isinstance(psd_raw, str):
            self._player_data = json.loads(psd_raw)
        else:
            self._player_data = psd_raw

        return self._player_data

    @property
    def player_data(self) -> dict[str, Any]:
        if self._player_data is None:
            self.decrypt()
        return self._player_data

    def get_item_save_datas(self) -> list[dict[str, Any]]:
        return self.player_data.get("itemSaveDatas", [])

    def get_inventory_save_datas(self) -> list[dict[str, Any]]:
        return self.player_data.get("inventorySaveDatas", [])

    def get_hero_save_datas(self) -> list[dict[str, Any]]:
        return self.player_data.get("heroSaveDatas", [])

    def get_all_item_keys(self) -> set[int]:
        keys = set()
        for item in self.get_item_save_datas():
            item_key = item.get("ItemKey")
            if item_key:
                keys.add(item_key)
        return keys

    def get_tradable_items(self) -> list[dict[str, Any]]:
        result = []
        seen_keys = set()

        for item in self.get_item_save_datas():
            item_key = item.get("ItemKey")
            if not item_key:
                continue

            if item_key in seen_keys:
                continue
            seen_keys.add(item_key)

            if not is_item_tradable(item_key):
                continue

            db_item = get_item(item_key)
            if not db_item:
                continue

            market_name = build_market_name(db_item)
            if not market_name:
                continue

            result.append({
                "item_key": item_key,
                "name": db_item["name"],
                "grade": db_item.get("grade", ""),
                "type": db_item["type"],
                "market_hash_name": market_name,
                "appid": STEAM_APPID_TBH,
            })

        return result

    def get_collected_items_for_import(self) -> list[dict[str, Any]]:
        equipped_uids = set()
        for hero in self.get_hero_save_datas():
            for uid in hero.get("equippedItemIds", []):
                if uid:
                    equipped_uids.add(uid)

        stash_uids = set()
        for stash in self.player_data.get("stashSaveDatas", []):
            uid = stash.get("ItemUniqueId")
            if uid:
                stash_uids.add(uid)

        item_uid_map: dict[int, int] = {}
        for item in self.get_item_save_datas():
            uid = item.get("UniqueId")
            item_key = item.get("ItemKey")
            if uid and item_key:
                item_uid_map[uid] = item_key

        seen_keys = set()
        for uid, item_key in item_uid_map.items():
            db_item = get_item(item_key)
            if not db_item:
                continue

            if not db_item.get("tradable"):
                continue

            if item_key in seen_keys:
                continue
            seen_keys.add(item_key)

            quantity = sum(
                1 for it in self.get_item_save_datas()
                if it.get("ItemKey") == item_key
            )

            market_name = build_market_name(db_item)
            if not market_name:
                continue

            yield {
                "item_key": item_key,
                "market_hash_name": market_name,
                "name": db_item["name"],
                "grade": db_item.get("grade", ""),
                "type": db_item["type"],
                "appid": STEAM_APPID_TBH,
                "quantity": quantity,
                "is_equipped": uid in equipped_uids,
                "is_in_stash": uid in stash_uids,
            }
