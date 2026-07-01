# Task Bar Hero — Estrutura do Save File

## Visão Geral da Estrutura

O save file do Task Bar Hero (`SaveFile_Live.es3`) é criptografado com ES3 e contém múltiplas estruturas de dados para armazenar diferentes aspectos do jogo.

---

## Estruturas Principais do `player_data`

### 1. `itemSaveDatas` (217 itens no save atual)
**O que é:** Lista geral de **todos os itens** que o jogador possui.

**Estrutura de cada item:**
```json
{
  "ItemKey": 314171,
  "UniqueId": 514119694408175373,
  "ItemName": "Shadow Bow",
  "Grade": "IMMORTAL",
  "ItemType": "GEAR",
  ...
}
```

**Importante:** Esta lista contém TODOS os itens, mas NÃO indica onde eles estão localizados. Para saber a localização, é necessário cruzar com as outras estruturas.

---

### 2. `stashSaveDatas` (343 slots, 145 ocupados no save atual)
**O que é:** Lista de **slots individuais do stash** (baú/armazém).

**Estrutura de cada slot:**
```json
{
  "Index": 1,
  "ItemUniqueId": 514119694408175373,
  "IsUnLock": true
}
```

**Detalhes importantes:**
- Cada entrada é um **slot individual**, não uma página completa
- O jogo tem 343 slots de stash no total (não "343 páginas")
- Cada slot pode estar vazio ou conter um item
- `IsUnLock: true` indica que o slot está desbloqueado
- `ItemUniqueId` referencia o `UniqueId` do item em `itemSaveDatas`

**Como verificar se um item está no stash:**
```python
stash_uids = {s.get('ItemUniqueId') for s in stashSaveDatas if s.get('ItemUniqueId')}
if item_uid in stash_uids:
    # Item está no stash
    # Para achar o slot exato:
    for i, slot in enumerate(stashSaveDatas, 1):
        if slot.get('ItemUniqueId') == item_uid:
            print(f"Item está no slot {i} do stash")
```

---

### 3. `inventorySaveDatas` (260 slots no save atual)
**O que é:** Inventário principal do jogador.

**Estrutura de cada slot:**
```json
{
  "Index": 0,
  "ItemUniqueId": 123456789,
  "IsUnlock": true,
  "IsUnlockedByRune": false
}
```

**Detalhes:**
- São os itens que estão "na mão" do jogador
- Prontos para serem equipados ou usados
- Não estão no stash e não estão equipados

---

### 4. `heroSaveDatas` (6 heróis no save atual)
**O que é:** Dados de cada herói, incluindo itens equipados.

**Estrutura de cada herói:**
```json
{
  "HeroName": "Explorer",
  "equippedItemIds": [514119694408175373, ...],
  ...
}
```

**Detalhes:**
- `equippedItemIds` é uma **lista de UniqueIds** dos itens equipados
- Cada herói pode ter múltiplos itens equipados (até 10 no save atual)

---

## Algoritmo para Determinar Localização de um Item

Dado um `ItemKey` ou `UniqueId`, siga esta lógica:

```python
def encontrar_localizacao(item_uid, items, stashes, heroes):
    """
    Determina onde um item está localizado.
    
    Args:
        item_uid: UniqueId do item procurado
        items: lista de itemSaveDatas
        stashes: lista de stashSaveDatas
        heroes: lista de heroSaveDatas
    
    Returns:
        str: Localização do item
    """
    
    # 1. Verificar se está no stash
    for i, slot in enumerate(stashes, 1):
        if slot.get('ItemUniqueId') == item_uid:
            return f"STASH slot {i}"
    
    # 2. Verificar se está equipado
    for hero in heroes:
        if item_uid in hero.get('equippedItemIds', []):
            return f"EQUIPADO em {hero.get('HeroName', 'Herói')}"
    
    # 3. Se não está no stash nem equipado, está no inventário principal
    return "INVENTÁRIO PRINCIPAL"
```

---

## Exemplo Prático: Localizando 3 Arcos

No save atual, temos:

| Item | ItemKey | UniqueId | Localização |
|------|---------|----------|-------------|
| Shadow Bow IMORTAL | 314171 | 514119694408175373 | **STASH slot 3** |
| Shadow Bow LENDÁRIO | 313171 | (outro UID) | **INVENTÁRIO PRINCIPAL** |
| Shadow Bow BEYOND | 315171 | — | Não encontrado |

**Fluxo de verificação:**
1. Buscar o item em `itemSaveDatas` pelo `ItemKey`
2. Pegar o `UniqueId` do item encontrado
3. Verificar se o `UniqueId` está em algum slot de `stashSaveDatas`
4. Se não, verificar se está em `equippedItemIds` de algum herói
5. Se não, está no `inventorySaveDatas` (inventário principal)

---

## Resumo das Estruturas

| Estrutura | Qtd Atual | Finalidade | Contém |
|-----------|-----------|------------|--------|
| `itemSaveDatas` | 217 | Catálogo de todos os itens | Dados completos de cada item |
| `stashSaveDatas` | 343 slots (145 ocupados) | Armazenamento (baú) | Slots com `ItemUniqueId` |
| `inventorySaveDatas` | 260 slots | Inventário principal | Slots com `ItemUniqueId` |
| `heroSaveDatas` | 6 heróis | Dados dos heróis | Lista `equippedItemIds` |

---

## Glossário

- **ItemKey:** ID do tipo do item (ex: 314171 = Shadow Bow IMORTAL)
- **UniqueId:** ID único de cada instância do item (cada item tem um UID diferente)
- **Stash:** Baú/armazém do jogo
- **Inventário Principal:** Itens que estão "na mão", prontos para usar
- **Equipado:** Item que está sendo usado por um herói

---

## Notas Importantes

1. **Nunca confie apenas em `itemSaveDatas`** para localização — ele só lista os itens, não diz onde estão.

2. **Sempre cruze os dados** entre as 4 estruturas para determinar a localização exata.

3. **A ordem de verificação importa:**
   - Primeiro verifique stash (mais específico)
   - Depois verifique equipados
   - Por fim, inventário principal (default)

4. **Slots vazios:** Um slot no `stashSaveDatas` ou `inventorySaveDatas` pode não ter `ItemUniqueId` (slot vazio).

5. **IsUnLock/IsUnlock:** Indica se o slot está desbloqueado. Slots bloqueados não podem conter itens.

---

## Código de Exemplo Completo

```python
from app.utils.save_parser import SaveParser
from pathlib import Path

save_path = Path('SaveFile_Live.es3')
parser = SaveParser(save_path)
parser.decrypt()

items = parser.get_item_save_datas()
stashes = parser.player_data.get('stashSaveDatas', [])
heroes = parser.get_hero_save_datas()

# Criar índice de stash UIDs para busca rápida
stash_uid_map = {
    s.get('ItemUniqueId'): i 
    for i, s in enumerate(stashes, 1) 
    if s.get('ItemUniqueId')
}

def localizar_item_por_key(item_key: int) -> str:
    """Encontra a localização de um item pelo ItemKey."""
    # 1. Achar o item na lista geral
    item = next((i for i in items if i.get('ItemKey') == item_key), None)
    if not item:
        return "NÃO ENCONTRADO"
    
    uid = item.get('UniqueId')
    
    # 2. Verificar stash
    if uid in stash_uid_map:
        return f"STASH slot {stash_uid_map[uid]}"
    
    # 3. Verificar equipados
    for hero in heroes:
        if uid in hero.get('equippedItemIds', []):
            return f"EQUIPADO em {hero.get('HeroName', 'Herói')}"
    
    # 4. Default: inventário principal
    return "INVENTÁRIO PRINCIPAL"

# Exemplo de uso
print(localizar_item_por_key(314171))  # Shadow Bow IMORTAL
# Saída: "STASH slot 3"
```