#!/usr/bin/env python3
# verify_inventory_assetids.py - Verificar AssetIDs válidos

import asyncio
import json
import logging
import os
from dotenv import load_dotenv
from services.inventory_service import InventoryService

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)

load_dotenv()

async def verify_inventory_assetids():
    """Verificar AssetIDs válidos no inventário"""
    
    print(" === VERIFICANDO ASSETIDS DO INVENTÁRIO ===")
    
    # Steam ID do usuário de teste
    steam_id = "76561199063085722"
    
    # Inicializar serviço de inventário
    inventory_service = InventoryService()
    
    print(f" Buscando inventário para Steam ID: {steam_id}")
    
    # Buscar inventário atual
    inventory_items = inventory_service.get_user_inventory(steam_id)
    
    if not inventory_items:
        print(" Nenhum item encontrado no inventário")
        return
    
    print(f" {len(inventory_items)} itens encontrados no inventário")
    print("\n === LISTA DE ITENS NEGOCIÁVEIS ===")
    
    tradable_items = []
    non_tradable_items = []
    
    for item in inventory_items:
        if item.tradable:
            tradable_items.append(item)
            print(f" NEGOCIÁVEL: {item.assetid} - {item.name}")
        else:
            non_tradable_items.append(item)
            print(f" NÃO-NEGOCIÁVEL: {item.assetid} - {item.name}")
    
    print(f"\n === RESUMO ===")
    print(f" Itens negociáveis: {len(tradable_items)}")
    print(f" Itens não-negociáveis: {len(non_tradable_items)}")
    
    if tradable_items:
        print(f"\n === ASSETIDS VÁLIDOS PARA TESTE ===")
        for i, item in enumerate(tradable_items[:3]):  # Primeiros 3 itens
            print(f"{i+1}. AssetID: {item.assetid} - {item.name}")
        
        print(f"\n Use estes AssetIDs para testar a trade offer:")
        valid_assetids = [item.assetid for item in tradable_items[:2]]
        print(f"AssetIDs recomendados: {valid_assetids}")
    else:
        print("\n Nenhum item negociável encontrado no inventário")

if __name__ == "__main__":
    asyncio.run(verify_inventory_assetids())
