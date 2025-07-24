#!/usr/bin/env python3
"""
TESTE COM ITENS REAIS E NEGOCIÁVEIS
Permite inserir asset IDs reais para testar trading
"""
import asyncio
import json
import os
from aiosteampy.client import SteamClient
from aiosteampy.models import EconItem
from aiosteampy.constants import AppContext

async def testar_com_itens_reais():
    print("🎯 TESTE COM ITENS REAIS E NEGOCIÁVEIS")
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
        
        # COLOQUE AQUI OS ASSET IDs DOS SEUS ITENS REAIS
        print("\n📋 CONFIGURE SEUS ITENS REAIS AQUI:")
        print("   Substitua os asset_ids abaixo pelos seus itens reais do CS2")
        print("   Para encontrar: Steam > Inventário > CS2 > Inspect > URL tem o asset ID")
        print()
        
        # SEUS ITENS REAIS - SUBSTITUA AQUI! 
        seus_itens_reais = [
            # Exemplo: "76561198123456789123456"
            # COLE SEUS ASSET IDs AQUI:
            "42136080323",  # Vírgula adicionada
            # Adicione mais se quiser
        ]
        
        # Seu partner steam ID (para quem enviar)
        # Pode ser sua própria conta ou outra para teste
        partner_steam_id = "76561198074635509"  # SUBSTITUA pelo SteamID do destinatário
        
        print(f"🎯 Testando envio de {len(seus_itens_reais)} itens para {partner_steam_id}")
        
        # Verificar se você preencheu os itens
        if seus_itens_reais[0] == "SUBSTITUA_PELO_SEU_ASSET_ID_1":
            print("❌ ATENÇÃO: Você precisa substituir os asset IDs pelos seus itens reais!")
            print("\n📝 COMO ENCONTRAR ASSET IDs:")
            print("1. Abra Steam")
            print("2. Vá para Inventário > CS2")
            print("3. Clique em qualquer item")
            print("4. Na URL que abrir, procure por números longos")
            print("5. Exemplo: steam://rungame/730/76561202255233023/+csgo_econ_action_preview%20S76561198123456789A42136080323D9889791121614972426")
            print("6. O asset ID é: 42136080323 (números após o 'A')")
            print("\n🔄 Execute novamente depois de configurar os asset IDs!")
            return
        
        # Criar EconItems com seus itens reais
        econ_items = []
        
        class ItemDescription:
            def __init__(self):
                self.market_tradable_restriction = 0
                self.market_marketable_restriction = 0
                self.name = "CS2 Item Real"
                self.type = "Weapon"
                self.tradable = True
                self.marketable = True
        
        for asset_id in seus_itens_reais:
            if asset_id.startswith("SUBSTITUA"):
                continue  # Pular items não configurados
                
            try:
                description = ItemDescription()
                
                econ_item = EconItem(
                    asset_id=str(asset_id),
                    owner_id=str(client.steam_id),  # Você é o owner
                    app_context=AppContext.CS2,
                    amount=1,
                    description=description
                )
                
                econ_items.append(econ_item)
                print(f"✅ EconItem criado para asset ID: {asset_id}")
                
            except Exception as e:
                print(f"❌ Erro criando EconItem para {asset_id}: {e}")
        
        if not econ_items:
            print("❌ Nenhum item válido foi configurado!")
            return
        
        # TESTE 1: Enviar seus itens (você dá, partner recebe)
        print(f"\n🚀 TESTE 1: ENVIANDO SEUS {len(econ_items)} ITENS REAIS...")
        try:
            result = await client.make_trade_offer(
                obj=int(partner_steam_id),
                to_give=econ_items,     # VOCÊ dá seus itens
                to_receive=[],          # VOCÊ não recebe nada
                message="Teste com itens reais - enviando meus itens",
                confirm=False
            )
            
            print(f"🎉 SUCESSO! Trade offer criada: {result}")
            
            # Se chegou aqui, o problema foi resolvido!
            print("\n✅ PROBLEMA RESOLVIDO!")
            print("   Seus itens são válidos e negociáveis")
            print("   O sistema de trading está funcionando")
            print("   Você pode usar a aplicação normalmente")
            
            return result
            
        except Exception as e:
            error_str = str(e)
            print(f"❌ Erro enviando seus itens: {e}")
            
            if "500" in error_str:
                print("\n🚨 AINDA ERRO 500 - VAMOS TENTAR OUTRAS ABORDAGENS...")
                
                # TESTE 2: Tentar receber itens em vez de enviar
                print("\n🔄 TESTE 2: TENTANDO RECEBER ITENS...")
                try:
                    # Criar items fake para "receber"
                    fake_item = EconItem(
                        asset_id="999999999",
                        owner_id=str(partner_steam_id),
                        app_context=AppContext.CS2,
                        amount=1,
                        description=ItemDescription()
                    )
                    
                    result = await client.make_trade_offer(
                        obj=int(partner_steam_id),
                        to_give=[],           # VOCÊ não dá nada
                        to_receive=[fake_item],  # VOCÊ recebe item
                        message="Teste recebendo item",
                        confirm=False
                    )
                    
                    print(f"✅ SUCESSO RECEBENDO! Trade offer: {result}")
                    return result
                    
                except Exception as e2:
                    print(f"❌ Erro recebendo também: {e2}")
                
                # TESTE 3: Verificar se é problema de parceiro
                print("\n🔄 TESTE 3: TESTANDO COM DIFERENTES PARCEIROS...")
                test_partners = [
                    "76561198074635509",  # Seu próprio ID
                    str(client.steam_id),  # Steam ID do bot
                ]
                
                for test_partner in test_partners:
                    try:
                        result = await client.make_trade_offer(
                            obj=int(test_partner),
                            to_give=econ_items[:1],  # Apenas 1 item
                            to_receive=[],
                            message=f"Teste com parceiro {test_partner}",
                            confirm=False
                        )
                        
                        print(f"✅ SUCESSO com parceiro {test_partner}!")
                        return result
                        
                    except Exception as e3:
                        print(f"❌ Falhou com parceiro {test_partner}: {e3}")
        
        print("\n💔 TODOS OS TESTES FALHARAM")
        print("🚨 CAUSA PROVÁVEL: LIMITAÇÃO DE TRADING DA CONTA")
        print("\n📋 SOLUÇÕES DEFINITIVAS:")
        print("1. 💰 Gaste EXATAMENTE $5.00 na Steam Store")
        print("2. 📱 Confirme Steam Guard Mobile ativo há 15+ dias")  
        print("3. ⏱️ Aguarde período de cooldown se mudou algo recentemente")
        print("4. 🔓 Mantenha perfil e inventário PÚBLICOS")
        print("5. 🎮 Confirme que não é uma conta 'Limited User'")
        
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
    asyncio.run(testar_com_itens_reais())
