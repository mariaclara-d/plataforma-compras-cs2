#!/usr/bin/env python3
"""
Script para verificar limitações específicas de trading no Steam
"""
import asyncio
import json
import os
import aiohttp
from aiosteampy.client import SteamClient
from dotenv import load_dotenv

load_dotenv()

async def verificar_limitacoes_steam():
    """Verifica limitações específicas de trading"""
    print("🔍 VERIFICANDO LIMITAÇÕES ESPECÍFICAS DA CONTA STEAM...")
    
    try:
        # Carregar credenciais
        with open("steam_guard.json", "r") as f:
            steam_guard = json.load(f)
        
        print(f"✅ Conta: {steam_guard['account_name']}")
        print(f"✅ Steam ID: {steam_guard['steam_id']}")
        
        # Criar cliente
        client = SteamClient(
            steam_id=steam_guard["steam_id"],
            username=steam_guard["account_name"],
            password=steam_guard["password"],
            shared_secret=steam_guard["shared_secret"],
            identity_secret=steam_guard["identity_secret"],
            api_key=os.getenv("STEAM_API_KEY")
        )
        
        # Login
        print("\n🔐 FAZENDO LOGIN...")
        await client.login()
        print("✅ Login realizado com sucesso!")
        
        # TESTE 1: Verificar se consegue acessar a página de trade offers
        print("\n🌐 TESTE 1: VERIFICANDO ACESSO À PÁGINA DE TRADE OFFERS...")
        try:
            async with aiohttp.ClientSession() as session:
                # Usar cookies de sessão do cliente aiosteampy
                cookies = client.session.cookie_jar
                
                # Tentar acessar a página de trade offers
                async with session.get(
                    'https://steamcommunity.com/my/tradeoffers/',
                    cookies=cookies,
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    }
                ) as resp:
                    content = await resp.text()
                    print(f"✅ Página de trade offers acessível: Status {resp.status}")
                    
                    # Verificar se há mensagens de limitação
                    if "trade ban" in content.lower():
                        print("❌ TRADE BAN detectado na página!")
                    elif "limited" in content.lower():
                        print("❌ Conta limitada detectada!")
                    elif "restricted" in content.lower():
                        print("❌ Conta restrita detectada!")
                    elif "eligible" in content.lower() and "not" in content.lower():
                        print("❌ Não elegível para trading!")
                    else:
                        print("✅ Nenhuma limitação óbvia detectada na página")
                        
        except Exception as e:
            print(f"❌ Erro ao acessar página: {e}")
        
        # TESTE 2: Verificar status específico da API
        print("\n📊 TESTE 2: VERIFICANDO STATUS VIA API STEAM...")
        try:
            steam_api_key = os.getenv("STEAM_API_KEY")
            if steam_api_key:
                async with aiohttp.ClientSession() as session:
                    # Verificar informações do jogador
                    url = f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={steam_api_key}&steamids={steam_guard['steam_id']}"
                    async with session.get(url) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            player = data.get('response', {}).get('players', [{}])[0]
                            
                            print(f"✅ Profile State: {player.get('profilestate', 'N/A')}")
                            print(f"✅ Community Visibility: {player.get('communityvisibilitystate', 'N/A')}")
                            print(f"✅ Profile Setup: {player.get('profileurl', 'N/A')}")
                            
                            # Verificar se o perfil é público
                            if player.get('communityvisibilitystate') != 3:
                                print("⚠️ PERFIL NÃO É PÚBLICO! Isso pode afetar trading.")
                        else:
                            print(f"❌ Erro na API Steam: Status {resp.status}")
            else:
                print("❌ Steam API Key não encontrada")
                
        except Exception as e:
            print(f"❌ Erro na verificação via API: {e}")
        
        # TESTE 3: Tentar verificar limitações de trading específicas
        print("\n🛡️ TESTE 3: VERIFICANDO LIMITAÇÕES DE TRADING...")
        try:
            # Tentar acessar a página de configurações de trading
            async with aiohttp.ClientSession() as session:
                cookies = client.session.cookie_jar
                
                async with session.get(
                    'https://steamcommunity.com/my/edit/settings',
                    cookies=cookies,
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    }
                ) as resp:
                    content = await resp.text()
                    print(f"✅ Página de configurações acessível: Status {resp.status}")
                    
                    # Procurar por indicações de limitações
                    if "trading is disabled" in content.lower():
                        print("❌ TRADING DESABILITADO!")
                    elif "mobile authenticator" in content.lower():
                        print("ℹ️ Referência ao Mobile Authenticator encontrada")
                    elif "steam guard" in content.lower():
                        print("ℹ️ Referência ao Steam Guard encontrada")
                        
        except Exception as e:
            print(f"❌ Erro ao verificar configurações: {e}")
        
        # TESTE 4: Verificar se consegue fazer uma ação simples de trading
        print("\n🔄 TESTE 4: VERIFICANDO CAPACIDADE DE TRADING...")
        try:
            # Tentar obter trade offers existentes
            trade_offers = await client.get_trade_offers()
            
            if isinstance(trade_offers, tuple):
                sent, received = trade_offers
                print(f"✅ Trade offers obtidas - Enviadas: {len(sent)}, Recebidas: {len(received)}")
            else:
                print(f"✅ Trade offers obtidas: {trade_offers}")
                
        except Exception as e:
            print(f"❌ Erro ao obter trade offers: {e}")
            error_str = str(e).lower()
            
            if "403" in error_str:
                print("❌ ERRO 403: Acesso negado - possível limitação de conta!")
            elif "500" in error_str:
                print("❌ ERRO 500: Erro interno do Steam")
            elif "unauthorized" in error_str:
                print("❌ NÃO AUTORIZADO: Possível problema de autenticação")
        
        # TESTE 5: Verificar se a conta tem histórico de compras
        print("\n💰 TESTE 5: VERIFICANDO HISTÓRICO...")
        try:
            # Verificar se consegue acessar histórico da carteira
            async with aiohttp.ClientSession() as session:
                cookies = client.session.cookie_jar
                
                async with session.get(
                    'https://store.steampowered.com/account/',
                    cookies=cookies,
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    }
                ) as resp:
                    content = await resp.text()
                    print(f"✅ Página da conta acessível: Status {resp.status}")
                    
                    if "limited user account" in content.lower():
                        print("❌ CONTA LIMITADA detectada!")
                    elif "restricted" in content.lower():
                        print("❌ CONTA RESTRITA detectada!")
                    else:
                        print("✅ Nenhuma limitação óbvia na conta")
                        
        except Exception as e:
            print(f"❌ Erro ao verificar conta: {e}")
        
        print("\n🏁 VERIFICAÇÃO CONCLUÍDA!")
        
        # Logout
        await client.logout()
        print("✅ Logout realizado")
        
    except Exception as e:
        print(f"❌ ERRO GERAL: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verificar_limitacoes_steam())
