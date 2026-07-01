from app.utils.save_parser import SaveParser
from pathlib import Path

save_path = Path('SaveFile_Live.es3')
parser = SaveParser(save_path)
parser.decrypt()

inventory = parser.player_data.get('inventorySaveDatas', [])
items = parser.get_item_save_datas()
stashes = parser.player_data.get('stashSaveDatas', [])
heroes = parser.get_hero_save_datas()

print(f'inventorySaveDatas: {len(inventory)} itens')
print(f'itemSaveDatas: {len(items)} itens')
print(f'stashSaveDatas: {len(stashes)} itens')

# Verificar estrutura de inventory
if inventory:
    print('\nEstrutura do primeiro item do inventory:')
    inv0 = inventory[0]
    print(f'  Chaves: {list(inv0.keys())}')

# Verificar estrutura de stash
if stashes:
    print('\nEstrutura do primeiro stash:')
    stash0 = stashes[0]
    print(f'  Chaves: {list(stash0.keys())}')

# Cruzar dados
stash_uids = {s.get('ItemUniqueId') for s in stashes if s.get('ItemUniqueId')}
print(f'\nUniqueIds no stash: {len(stash_uids)}')

# Buscar os 3 arcos
arcos = {
    314171: 'Shadow Bow IMORTAL',
    313171: 'Shadow Bow LENDARIO', 
    315171: 'Shadow Bow BEYOND'
}

print('\n=== Localizacao dos arcos ===')
for key, nome in arcos.items():
    for item in items:
        if item.get('ItemKey') == key:
            uid = item.get('UniqueId')
            
            # Verifica se esta no stash
            if uid in stash_uids:
                for i, s in enumerate(stashes, 1):
                    if s.get('ItemUniqueId') == uid:
                        print(f'{nome} (Key {key}): STASH slot {i}')
                        break
            else:
                # Verifica se esta equipado
                equipado = False
                for hero in heroes:
                    if uid in hero.get('equippedItemIds', []):
                        print(f'{nome} (Key {key}): EQUIPADO em {hero.get("HeroName")}')
                        equipado = True
                        break
                
                # Se nao esta no stash nem equipado, esta no inventario
                if not equipado:
                    print(f'{nome} (Key {key}): INVENTARIO PRINCIPAL')