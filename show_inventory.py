from app.utils.save_parser import SaveParser
from app.utils.item_db import get_item
from pathlib import Path

save_path = Path('SaveFile_Live.es3')
parser = SaveParser(save_path)
parser.decrypt()

items = parser.get_item_save_datas()
stashes = parser.player_data.get('stashSaveDatas', [])
heroes = parser.get_hero_save_datas()

# Criar conjunto de UIDs que estão no stash
stash_uids = {s.get('ItemUniqueId') for s in stashes if s.get('ItemUniqueId')}

# Criar conjunto de UIDs que estão equipados
equipped_uids = set()
for hero in heroes:
    equipped_uids.update(hero.get('equippedItemIds', []))

# Filtrar itens do inventário principal
# (estão em itemSaveDatas mas NÃO estão no stash e NÃO estão equipados)
inventory_items = []
for item in items:
    uid = item.get('UniqueId')
    if not uid:
        continue
    
    # Ignorar UIDs zerados (slots vazios)
    if uid == 0:
        continue
    
    # Se está no stash ou equipado, não está no inventário principal
    if uid in stash_uids or uid in equipped_uids:
        continue
    
    inventory_items.append(item)

print("=" * 80)
print("ITENS NO INVENTÁRIO PRINCIPAL")
print("=" * 80)
print(f"Total de itens: {len(inventory_items)}\n")

# Agrupar por tipo
from collections import defaultdict
by_type = defaultdict(list)
for item in inventory_items:
    item_key = item.get('ItemKey')
    db_item = get_item(item_key)
    item_type = db_item.get('type', 'UNKNOWN') if db_item else 'UNKNOWN'
    by_type[item_type].append((item, db_item))

# Mostrar por tipo
type_order = ['GEAR', 'MATERIAL', 'STAGEBOX', 'CONSUMABLE', 'UNKNOWN']
for item_type in type_order:
    type_items = by_type.get(item_type, [])
    if not type_items:
        continue
    
    print(f"\n{item_type} ({len(type_items)} itens):")
    print("-" * 80)
    
    for i, (item, db_item) in enumerate(type_items, 1):
        item_key = item.get('ItemKey')
        uid = item.get('UniqueId')
        
        if db_item:
            name = db_item['name']
            grade = db_item.get('grade', '')
            tradable = "✅" if db_item.get('tradable') else "❌"
            print(f"  {i:3d}. {name} ({grade}) [Key: {item_key}] [UID: {uid}] {tradable}")
        else:
            item_name = item.get('ItemName', 'Desconhecido')
            grade = item.get('Grade', '')
            print(f"  {i:3d}. {item_name} ({grade}) [Key: {item_key}] [UID: {uid}]")

print("\n" + "=" * 80)
print(f"Total no inventário principal: {len(inventory_items)}")
print(f"  - Gear: {len(by_type.get('GEAR', []))}")
print(f"  - Material: {len(by_type.get('MATERIAL', []))}")
print(f"  - Outros: {sum(len(v) for k, v in by_type.items() if k not in ['GEAR', 'MATERIAL'])}")
print("=" * 80)

# Mostrar apenas os tradaveis
print("\n=== ITENS TRADABLES (podem ser vendidos no mercado) ===")
tradables = []
for item in inventory_items:
    item_key = item.get('ItemKey')
    db_item = get_item(item_key)
    if db_item and db_item.get('tradable'):
        tradables.append((item, db_item))

print(f"Total de itens tradables: {len(tradables)}\n")

for i, (item, db_item) in enumerate(tradables, 1):
    item_key = item.get('ItemKey')
    name = db_item['name']
    grade = db_item.get('grade', '')
    print(f"  {i:3d}. {name} ({grade}) [Key: {item_key}]")