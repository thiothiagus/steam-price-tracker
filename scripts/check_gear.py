from app.utils.save_parser import SaveParser

parser = SaveParser('C:\\Apps\\steam-price-tracker\\SaveFile_Live.es3')
parser.decrypt()

items = list(parser.get_collected_items_for_import())
print(f"Total items to import: {len(items)}")
for item in items:
    print(f'{item["market_hash_name"]} -> type={item.get("type")}, gear_type={item.get("gear_type")}, gear_level={item.get("gear_level")}, equipped={item.get("is_equipped")}')