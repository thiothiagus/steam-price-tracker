from app.utils.save_parser import SaveParser
from app.utils.item_db import get_all_tradable_items
from pathlib import Path

save_path = Path('SaveFile_Live.es3')
parser = SaveParser(save_path)
parser.decrypt()

items = parser.get_item_save_datas()
heroes = parser.get_hero_save_datas()
stashes = parser.player_data.get('stashSaveDatas', [])

# Shadow Bow Imortal = 314171
TARGET_KEY = 314171
TARGET_NAME = "Shadow Bow (IMMORTAL)"

print(f"=== Buscando: {TARGET_NAME} (Key: {TARGET_KEY}) ===\n")

# Encontrar todas as instancias do item
encontrados = []
for item in items:
    if item.get('ItemKey') == TARGET_KEY:
        encontrados.append(item)

print(f"Total encontrado: {len(encontrados)} unidade(s)\n")

for idx, item in enumerate(encontrados, 1):
    uid = item.get('UniqueId')
    print(f"--- Unidade {idx} ---")
    print(f"  UniqueId: {uid}")
    
    # Verificar se esta equipado em algum heroi
    equipado_em = None
    for hero in heroes:
        hero_name = hero.get('HeroName', 'Heroi Desconhecido')
        if uid in hero.get('equippedItemIds', []):
            equipado_em = hero_name
            break
    
    if equipado_em:
        print(f"  Local: EQUIPADO em {equipado_em}")
    else:
        # Verificar se esta no stash
        no_stash = False
        stash_idx = None
        for i, stash in enumerate(stashes, 1):
            stash_items = stash.get('itemSaveDatas', [])
            for stash_item in stash_items:
                if stash_item.get('UniqueId') == uid:
                    no_stash = True
                    stash_idx = i
                    break
            if no_stash:
                break
        
        if no_stash:
            print(f"  Local: No STASH (pagina {stash_idx})")
        else:
            print(f"  Local: No inventario principal")
    print()