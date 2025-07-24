#!/usr/bin/env python3
"""
DIAGNÓSTICO COMPLETO DE LIMITAÇÕES STEAM
Identifica exatamente qual limitação está afetando o trading
"""
import asyncio
import json
import os
from datetime import datetime
from aiosteampy.client import SteamClient

async def diagnosticar_limitacoes_steam():
    print("🔍 DIAGNÓSTICO COMPLETO DE LIMITAÇÕES STEAM")
    print("=" * 50)
    
    # Carregar steam guard
    with open('steam_guard.json', 'r') as f:
        steam_guard_data = json.load(f)
    
    client = SteamClient(
        steam_id=steam_guard_data["steam_id"],
        username=steam_guard_data["account_name"],
        password=steam_guard_data["password"],
        shared_secret=steam_guard_data["shared_secret"],
        identity_secret=steam_guard_data["identity_secret"],
        api_key=os.getenv("STEAM_API_KEY")
    )
    
    try:
        # Login
        print("🔐 Fazendo login...")
        await client.login()
        print("✅ Login realizado com sucesso!")
        
        steam_id = steam_guard_data["steam_id"]
        print(f"📋 Analisando conta: {steam_guard_data['account_name']} (ID: {steam_id})")
        print()
        
        # 1. VERIFICAR PERFIL PÚBLICO
        print("1️⃣ VERIFICANDO VISIBILIDADE DO PERFIL...")
        try:
            # Fazer requisição direta para o perfil via API Steam
            import aiohttp
            async with aiohttp.ClientSession() as session:
                url = f"http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/"
                params = {
                    'key': os.getenv("STEAM_API_KEY"),
                    'steamids': steam_id
                }
                async with session.get(url, params=params) as resp:
                    data = await resp.json()
                    
                    if data['response']['players']:
                        player = data['response']['players'][0]
                        visibility = player.get('communityvisibilitystate', 0)
                        
                        if visibility == 3:
                            print("✅ Perfil é PÚBLICO")
                        elif visibility == 1:
                            print("❌ Perfil é PRIVADO - PRECISA SER PÚBLICO PARA TRADING")
                        else:
                            print(f"⚠️ Visibilidade desconhecida: {visibility}")
                            
                        print(f"   Nome: {player.get('personaname', 'N/A')}")
                        print(f"   Estado: {player.get('personastate', 'N/A')}")
                        
                        # Verificar se tem avatar (indica conta ativa)
                        if player.get('avatar'):
                            print("✅ Conta tem avatar (ativa)")
                        else:
                            print("⚠️ Conta sem avatar")
                            
        except Exception as e:
            print(f"❌ Erro verificando perfil: {e}")
        
        print()
        
        # 2. VERIFICAR TRADE TOKEN
        print("2️⃣ VERIFICANDO TRADE TOKEN...")
        try:
            token = await client.get_trade_token()
            print(f"✅ Trade token válido: {token}")
        except Exception as e:
            print(f"❌ Erro obtendo trade token: {e}")
        
        print()
        
        # 3. VERIFICAR INVENTÁRIO CS2
        print("3️⃣ VERIFICANDO INVENTÁRIO CS2...")
        try:
            inventory = await client.get_inventory(730)  # CS2 = AppID 730
            if inventory:
                print(f"✅ Inventário CS2 acessível: {len(inventory)} itens")
                
                # Verificar itens tradeable
                tradeable_items = [item for item in inventory if getattr(item, 'tradable', True)]
                print(f"   Itens negociáveis: {len(tradeable_items)}")
                
                if tradeable_items:
                    print("   Exemplos de itens negociáveis:")
                    for i, item in enumerate(tradeable_items[:3]):
                        print(f"     {i+1}. {getattr(item, 'market_name', 'N/A')} (ID: {item.asset_id})")
                else:
                    print("❌ NENHUM ITEM NEGOCIÁVEL ENCONTRADO")
                    
            else:
                print("❌ Inventário vazio ou inacessível")
                
        except Exception as e:
            error_str = str(e)
            if "400" in error_str:
                print("❌ INVENTÁRIO PRIVADO ou CONTA LIMITADA")
            else:
                print(f"❌ Erro acessando inventário: {e}")
        
        print()
        
        # 4. VERIFICAR HISTÓRICO DE TRADES
        print("4️⃣ VERIFICANDO HISTÓRICO DE TRADES...")
        try:
            history = await client.get_trade_history()
            if history:
                print(f"✅ Histórico de trades acessível: {len(history)} trades")
                if len(history) > 0:
                    print("✅ Conta já fez trades antes (não limitada)")
                else:
                    print("⚠️ Nenhum trade anterior (pode ser limitação)")
            else:
                print("⚠️ Sem histórico de trades")
        except Exception as e:
            print(f"❌ Erro verificando histórico: {e}")
        
        print()
        
        # 5. VERIFICAR OFERTAS EXISTENTES
        print("5️⃣ VERIFICANDO OFERTAS DE TRADE...")
        try:
            offers = await client.get_trade_offers()
            print(f"✅ Sistema de trade offers funcionando")
            
            if isinstance(offers, tuple) and len(offers) >= 2:
                sent, received = offers[:2]
                print(f"   Ofertas enviadas: {len(sent) if hasattr(sent, '__len__') else 0}")
                print(f"   Ofertas recebidas: {len(received) if hasattr(received, '__len__') else 0}")
            
        except Exception as e:
            print(f"❌ Erro verificando ofertas: {e}")
        
        print()
        
        # 6. TESTE DE LIMITAÇÃO DIRETA
        print("6️⃣ TESTE DIRETO DE CRIAÇÃO DE TRADE OFFER...")
        try:
            # Tentar criar uma oferta vazia para ver o erro específico
            from aiosteampy.models import EconItem
            from aiosteampy.constants import AppContext
            
            # Criar item fake para teste
            class FakeDescription:
                def __init__(self):
                    self.market_tradable_restriction = 0
                    self.market_marketable_restriction = 0
                    self.name = "Test Item"
                    self.tradable = True
                    
            fake_item = EconItem(
                asset_id="999999999",
                owner_id=steam_id,
                app_context=AppContext.CS2,
                amount=1,
                description=FakeDescription()
            )
            
            result = await client.make_trade_offer(
                obj=int(steam_id),  # Para si mesmo (vai dar erro, mas vemos qual)
                to_give=[fake_item],
                to_receive=[],
                message="Teste de limitação",
                confirm=False
            )
            
            print("✅ Trade offer criada com sucesso (inesperado)")
            
        except Exception as e:
            error_str = str(e).lower()
            print(f"❌ Erro ao criar trade offer: {e}")
            
            # Analisar tipo específico de erro
            if "500" in error_str and "internal server error" in error_str:
                print("🚨 DIAGNÓSTICO: CONTA COM LIMITAÇÃO DE TRADING")
                print("   Possíveis causas:")
                print("   • Conta nova (menos de 15 dias com Steam Guard)")
                print("   • Menos de $5 gastos na Steam Store")
                print("   • Steam Guard mobile não ativado há 15+ dias")
                print("   • Conta considerada 'limited' pelo Steam")
                
            elif "you cannot trade" in error_str:
                print("🚨 DIAGNÓSTICO: TRADING DESABILITADO")
                
            elif "invalid partner" in error_str:
                print("⚠️ Erro de parceiro (normal para teste)")
                
            elif "empty trade" in error_str:
                print("⚠️ Erro de oferta vazia (normal)")
                
            else:
                print(f"🤔 Erro desconhecido: {error_str}")
        
        print()
        print("=" * 50)
        print("📋 RESUMO DO DIAGNÓSTICO:")
        print("1. Verifique se o perfil está público")
        print("2. Verifique se o inventário CS2 está público")
        print("3. Confirme que tem itens negociáveis")
        print("4. Para resolver limitação de trading:")
        print("   • Gaste pelo menos $5 na Steam Store")
        print("   • Ative Steam Guard mobile")
        print("   • Aguarde 15 dias após ativar Steam Guard")
        print("   • Mantenha perfil e inventário públicos")
        
    except Exception as e:
        print(f"❌ Erro geral: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        try:
            if hasattr(client, 'close'):
                await client.close()
            elif hasattr(client, 'logout'):
                await client.logout()
        except:
            pass

if __name__ == "__main__":
    asyncio.run(diagnosticar_limitacoes_steam())
