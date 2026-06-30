"""Script para baixar ícones dos itens negociáveis do TBH."""

import asyncio
import httpx
import json
from pathlib import Path

from app.utils.item_db import get_all_tradable_items, build_market_name


ICONS_DIR = Path(__file__).parent / "app" / "data" / "icons"
ICONS_DIR.mkdir(parents=True, exist_ok=True)


async def download_icon(
    session: httpx.AsyncClient,
    market_hash_name: str,
    icon_hash: str,
) -> bool:
    """Baixa o ícone de um item."""
    url = f"https://community.steamstatic.com/economy/image/{icon_hash}"
    
    try:
        response = await session.get(url)
        response.raise_for_status()
        
        # Salva o ícone
        filename = f"{market_hash_name.replace('/', '_')}.png"
        filepath = ICONS_DIR / filename
        
        with open(filepath, "wb") as f:
            f.write(response.content)
        
        return True
    except Exception as e:
        print(f"Erro ao baixar {market_hash_name}: {e}")
        return False


async def main():
    """Baixa todos os ícones dos itens negociáveis."""
    items = get_all_tradable_items()
    
    # Carrega hashes existentes
    hashes_path = Path(__file__).parent / "app" / "data" / "icon_hashes.json"
    with open(hashes_path, "r", encoding="utf-8") as f:
        icon_hashes = json.load(f)
    
    print(f"Total de itens negociáveis: {len(items)}")
    print(f"Ícones com hash disponível: {sum(1 for i in items if build_market_name(i) in icon_hashes)}")
    
    async with httpx.AsyncClient(
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        },
        timeout=30.0,
    ) as session:
        tasks = []
        for item in items:
            market_name = build_market_name(item)
            if not market_name:
                continue
            
            icon_hash = icon_hashes.get(market_name)
            if not icon_hash:
                print(f"Sem hash para: {market_name}")
                continue
            
            tasks.append(download_icon(session, market_name, icon_hash))
        
        print(f"\nBaixando {len(tasks)} ícones...")
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        success = sum(1 for r in results if r is True)
        failed = len(results) - success
        
        print(f"\nConcluído!")
        print(f"  Sucesso: {success}")
        print(f"  Falharam: {failed}")


if __name__ == "__main__":
    asyncio.run(main())