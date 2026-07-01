from app.utils.save_parser import SaveParser
from app.utils.item_db import get_item
from pathlib import Path

save_path = Path('SaveFile_Live.es3')
parser = SaveParser(save_path)
parser.decrypt()

items = parser.get_item_save_datas()
heroes = parser.get_hero_save_datas()

# Criar mapa de UniqueId -> Item
item_map = {}
for item in items:
    uid = item.get('UniqueId')
    if uid:
        item_map[uid] = item

print("=" * 80)
print("EQUIPAMENTOS DOS HERÓIS")
print("=" * 80)

for hero in heroes:
    hero_name = hero.get('HeroName', 'Herói Desconhecido')
    equipped_ids = hero.get('equippedItemIds', [])
    
    print(f"\n{hero_name}:")
    print(f"  Itens equipados: {len(equipped_ids)}")
    
    if not equipped_ids:
        print("  (nenhum item)")
        continue
    
    for i, uid in enumerate(equipped_ids, 1):
        item = item_map.get(uid)
        if item:
            item_key = item.get('ItemKey')
            item_name = item.get('ItemName', 'Desconhecido')
            grade = item.get('Grade', '')
            item_type = item.get('ItemType', '')
            
            # Buscar nome completo no banco
            db_item = get_item(item_key)
            if db_item:
                full_name = f"{db_item['name']} ({db_item.get('grade', grade)})"
            else:
                full_name = f"{item_name} ({grade})" if grade else item_name
            
            print(f"  {i:2d}. {full_name}")
            print(f"      Key: {item_key} | UID: {uid}")
        else:
            print(f"  {i:2d}. [Item não encontrado em itemSaveDatas]")
            print(f"      UID: {uid}")

print("\n" + "=" * 80)
print(f"Total de heróis: {len(heroes)}")
print(f"Total de itens equipados: {sum(len(h.get('equippedItemIds', [])) for h in heroes)}")
print("=" * 80)