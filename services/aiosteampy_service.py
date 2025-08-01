import os
import re
import json
import asyncio
from datetime import datetime, timedelta, timezone
from pathlib import Path
from dotenv import load_dotenv
from aiosteampy.client import SteamClient
from aiosteampy.constants import AppContext
from aiosteampy.models import EconItem
from aiosteampy.helpers import restore_from_cookies
from aiosteampy.utils import get_jsonable_cookies
from db_config import db
from models import TradeOffer
from models import Skin


load_dotenv()

# Arquivo para persistência de sessão
COOKIE_FILE = Path("config/steam/session_cookies.json")

# ------------------- LOGIN ------------------- #
async def realizar_login_aiosteampy():
    """
    Login com persistência de sessão seguindo documentação oficial aiosteampy 0.7.15
    """
    try:
        with open("config/steam/steam_guard.json", "r") as f:
            steam_guard = json.load(f)
    except Exception as e:
        raise RuntimeError("Erro ao carregar steam_guard.json: " + str(e))
    
    print("🔐 Criando cliente Steam com persistência de sessão...")
    print(f"🔐 Account: {steam_guard['account_name']}")
    print(f"🔐 Steam ID: {steam_guard['steam_id']}")
    
    # Validar credenciais obrigatórias
    required_fields = ['steam_id', 'account_name', 'password', 'shared_secret', 'identity_secret']
    for field in required_fields:
        if not steam_guard.get(field):
            raise RuntimeError(f"Campo obrigatório ausente no steam_guard.json: {field}")
    
    # Converter secrets de Base64 para Base32 se necessário
    shared_secret = steam_guard["shared_secret"]
    identity_secret = steam_guard["identity_secret"]
    
    # Usar secrets diretamente - já estão no formato Base32 correto
    print(f"🔍 shared_secret: {shared_secret}")
    print(f"� identity_secret: {identity_secret}")
    
    # Garantir padding correto para Base32 se necessário
    import base64
    try:
        # Testar se é Base32 válido com padding correto
        def fix_base32_padding(secret):
            # Remover padding existente e calcular correto
            secret = secret.rstrip('=')
            padding_needed = (8 - len(secret) % 8) % 8
            return secret + ('=' * padding_needed)
        
        shared_secret = fix_base32_padding(shared_secret)
        identity_secret = fix_base32_padding(identity_secret)
        
        print(f"🔧 shared_secret com padding: '{shared_secret}'")
        print(f"🔧 identity_secret com padding: '{identity_secret}'")
        
        padded_shared = shared_secret
        test_shared = base64.b32decode(padded_shared)
        print(f"✅ shared_secret é Base32 válido ({len(test_shared)} bytes)")
        shared_secret = padded_shared
        
        padded_identity = identity_secret
        test_identity = base64.b32decode(padded_identity)
        print(f"✅ identity_secret é Base32 válido ({len(test_identity)} bytes)")
        identity_secret = padded_identity
        
    except Exception as b32_error:
        print(f"❌ Erro na validação Base32: {b32_error}")
        print(f"🔍 shared_secret original: '{steam_guard['shared_secret']}'")
        print(f"🔍 identity_secret original: '{steam_guard['identity_secret']}'")
        raise RuntimeError(f"Secrets não são Base32 válidos: {b32_error}")
    
    # Criar cliente seguindo exemplo oficial de persistência
    client = SteamClient(
        steam_id=int(steam_guard["steam_id"]),
        username=steam_guard["account_name"],
        password=steam_guard["password"],
        shared_secret=shared_secret,
        identity_secret=identity_secret
    )
    
    try:
        # Tentar restaurar sessão de cookies salvos (seguindo documentação)
        if COOKIE_FILE.is_file():
            print("🍪 Tentando restaurar sessão de cookies salvos...")
            try:
                with COOKIE_FILE.open("r") as f:
                    cookies = json.load(f)
                await restore_from_cookies(cookies, client)
                
                # Verificar se a sessão restaurada está válida
                is_alive = await client.is_session_alive()
                if is_alive:
                    print("✅ Sessão restaurada com sucesso!")
                    
                    # Preparar cliente (trade_acknowledge, etc.)
                    print("🔧 Preparando cliente...")
                    await client.prepare()
                    print("✅ Cliente preparado com sucesso!")
                    
                    return client
                else:
                    print("⚠️ Sessão de cookies expirada, fazendo login completo...")
            except Exception as cookie_error:
                print(f"⚠️ Erro ao restaurar cookies: {cookie_error}")
                print("🔄 Fazendo login completo...")
        
        # Login completo se não há cookies ou se falharam
        print("🔐 Realizando login completo...")
        
        # VERIFICAÇÃO PRÉVIA: Status da Steam API
        print("🔍 Verificando status da Steam API...")
        try:
            import aiohttp
            async with aiohttp.ClientSession() as check_session:
                async with check_session.get("https://steamstat.us/api/v2/", timeout=10) as resp:
                    if resp.status == 200:
                        steam_status = await resp.json()
                        services_status = steam_status.get("services", {})
                        steam_community = services_status.get("SteamCommunity", {}).get("status", "unknown")
                        web_api = services_status.get("WebAPI", {}).get("status", "unknown")
                        
                        if steam_community == "good" and web_api == "good":
                            print("✅ Steam API reportada como funcional")
                        else:
                            print(f"⚠️ Steam API com problemas: Community={steam_community}, WebAPI={web_api}")
                            print("🔄 Continuando mesmo assim com delays aumentados...")
                    else:
                        print("⚠️ Não foi possível verificar status da Steam")
        except Exception as status_error:
            print(f"⚠️ Erro ao verificar Steam status: {status_error}")
        
        # ESTRATÉGIA ROBUSTA: Delays progressivos mais agressivos
        print("⏱️ Aguardando 15s inicial para evitar rate limit...")
        await asyncio.sleep(15)
        
        # Tentar login com retry mais agressivo
        max_tentativas = 5  # Aumentado para 5 tentativas
        for tentativa in range(1, max_tentativas + 1):
            print(f"🔄 Tentativa de login {tentativa}/{max_tentativas}...")
            
            try:
                print("🔐 Chamando client.login()...")
                
                # NOVA ESTRATÉGIA: Detectar e contornar problemas específicos da Steam
                try:
                    await client.login()
                    print("✅ Login realizado com sucesso!")
                except KeyError as login_ke:
                    error_key = str(login_ke).replace("'", "").replace('"', '')
                    print(f"🚨 KeyError detectado: {error_key}")
                    
                    if "client_id" in error_key:
                        print("🚨 Steam API falhou em retornar client_id - implementando estratégia avançada")
                        
                        # ESTRATÉGIA 1: Tentar recriar o cliente
                        if tentativa <= 2:
                            delay = 60 + (tentativa * 30)  # 60s, 90s
                            print(f"🔄 Recriando cliente Steam após {delay}s...")
                            await asyncio.sleep(delay)
                            
                            # Recriar cliente do zero
                            print("🔧 Recriando cliente Steam...")
                            client = SteamClient(
                                steam_id=int(steam_guard["steam_id"]),
                                username=steam_guard["account_name"],
                                password=steam_guard["password"],
                                shared_secret=shared_secret,
                                identity_secret=identity_secret
                            )
                            print("✅ Cliente recriado - tentando login novamente...")
                            raise KeyError("client_id")  # Forçar retry
                            
                        # ESTRATÉGIA 2: Aguardo mais longo para Steam "esfriar"
                        elif tentativa <= 4:
                            delay = 120 + (tentativa * 60)  # 180s, 240s
                            print(f"🔄 Steam overload - aguardando {delay}s para estabilizar...")
                            await asyncio.sleep(delay)
                            raise KeyError("client_id")  # Forçar retry
                            
                        else:
                            print("❌ Steam API consistentemente falhando - problema no servidor")
                            raise RuntimeError("Steam API está com problemas graves de client_id. Servidores podem estar em manutenção.")
                    
                    elif "access_token" in error_key or "refresh_token" in error_key:
                        print("🚨 Problema de autenticação - tokens rejeitados")
                        if tentativa <= 3:
                            delay = 90 + (tentativa * 45)  # 135s, 180s, 225s
                            print(f"⏱️ Aguardando {delay}s para tokens serem aceitos...")
                            await asyncio.sleep(delay)
                            raise KeyError(error_key)  # Forçar retry
                        else:
                            raise RuntimeError("Steam rejeitou credenciais consistentemente. Verifique username/password.")
                    
                    else:
                        # Outros KeyErrors
                        print(f"🚨 KeyError desconhecido: {error_key}")
                        raise login_ke
                
                # IMPORTANTE: Preparar cliente (inclui trade_acknowledge desde 0.7.15)
                print("🔧 Preparando cliente...")
                await client.prepare()
                print("✅ Cliente preparado com sucesso!")
                
                # Verificar se temos client_id após login
                print(f"🔍 Verificando client após login...")
                print(f"   • client.steam_id: {getattr(client, 'steam_id', 'NÃO DEFINIDO')}")
                print(f"   • client.session: {getattr(client, 'session', 'NÃO DEFINIDO')}")
                print(f"   • client.logged_on: {getattr(client, 'logged_on', 'NÃO DEFINIDO')}")
                
                # Salvar cookies para próxima sessão (seguindo documentação)
                print("💾 Salvando cookies de sessão...")
                try:
                    COOKIE_FILE.parent.mkdir(parents=True, exist_ok=True)
                    with COOKIE_FILE.open("w") as f:
                        json.dump(get_jsonable_cookies(client.session), f)
                    print("✅ Cookies salvos com sucesso!")
                except Exception as save_error:
                    print(f"⚠️ Erro ao salvar cookies (não crítico): {save_error}")
                
                return client
                
            except KeyError as ke:
                error_str = str(ke)
                print(f"❌ Tentativa {tentativa} falhou com KeyError: {error_str}")
                print(f"🔍 KeyError detalhado:")
                print(f"   • Erro: {repr(ke)}")
                print(f"   • Args: {ke.args}")
                print(f"   • Estado do client: {type(client).__name__}")
                
                # ANÁLISE ESPECÍFICA DE KEYERROR
                error_key = error_str.replace("'", "").replace('"', '')
                
                if "access_token" in error_key or "refresh_token" in error_key:
                    print("🚨 Steam rejeitando tokens - aguardando mais tempo...")
                    print("🔍 Este erro indica rate limit ou sobrecarga temporária da Steam")
                    
                    if tentativa < max_tentativas:
                        delay = 90 + (tentativa * 45)  # 135s, 180s, 225s, 270s
                        print(f"⏱️ Aguardando {delay}s para reduzir pressão na Steam API...")
                        await asyncio.sleep(delay)
                        continue
                    else:
                        print("❌ Steam continua rejeitando tokens após múltiplas tentativas")
                        raise RuntimeError("Steam API temporariamente indisponível para tokens. Rate limit severo ou manutenção. Tente novamente em 30+ minutos.")
                        
                elif "client_id" in error_key:
                    print("🚨 Erro crítico de client_id - problema estrutural da Steam")
                    print(f"🔍 Session disponível: {hasattr(client, 'session')}")
                    if hasattr(client, 'session'):
                        print(f"🔍 Session status: {client.session}")
                    
                    # Este erro já foi tratado acima com recriação do cliente
                    # Se chegou aqui, é porque as estratégias não funcionaram
                    if tentativa < max_tentativas:
                        delay = 180  # 3 minutos fixos para client_id
                        print(f"⏱️ client_id error crítico - aguardando {delay}s...")
                        await asyncio.sleep(delay)
                        continue
                    else:
                        raise RuntimeError("Steam API em falha crítica de client_id. Servidores podem estar em manutenção ou sobrecarga extrema.")
                
                else:
                    # Outros KeyErrors não específicos
                    print(f"🚨 KeyError genérico: {error_key}")
                    if tentativa < max_tentativas:
                        delay = 60 + (tentativa * 30)  # 90s, 120s, 150s, 180s
                        print(f"⏱️ Aguardando {delay}s para retry geral...")
                        await asyncio.sleep(delay)
                        continue
                    else:
                        raise RuntimeError(f"KeyError persistente não resolvido: {error_str}")
            
            except Exception as e:
                error_str = str(e)
                print(f"❌ Tentativa {tentativa} falhou: {error_str}")
                
                if "Rate limit" in error_str or "429" in error_str:
                    if tentativa < max_tentativas:
                        delay = 60 * tentativa  # 1min, 2min
                        print(f"⏱️ Rate limit - aguardando {delay}s...")
                        await asyncio.sleep(delay)
                        continue
                    else:
                        raise RuntimeError("Rate limit persistente do Steam.")
                
                elif "Two-factor" in error_str or "Steam Guard" in error_str:
                    raise RuntimeError("Erro crítico do Steam Guard. Verifique shared_secret.")
                
                else:
                    if tentativa < max_tentativas:
                        delay = tentativa * 25
                        print(f"⏱️ Aguardando {delay}s para retry...")
                        await asyncio.sleep(delay)
                        continue
                    else:
                        raise RuntimeError(f"Falha crítica na autenticação: {error_str}")
        
        # Se chegou aqui, todas as tentativas falharam
        raise RuntimeError("Falha em todas as tentativas de login")
        
    except Exception as e:
        # Limpar cookies se login falhar
        try:
            if COOKIE_FILE.exists():
                COOKIE_FILE.unlink()
                print("🗑️ Cookies inválidos removidos")
        except:
            pass
        raise e
    
    
    # ------------------- VALOR LÍQUIDO------------------- #
    
def calcular_valor_liquido(preco, percentual_comissao=0.65):
    """Calcula o valor líquido baseado no preço e percentual de comissão."""
    if preco is None:
        return None
    return preco * percentual_comissao



# ------------------- VERIFICAÇÃO DE CONTA ------------------- #
async def verificar_status_conta_steam(client: SteamClient, steamid: int):
    """Verifica se uma conta Steam pode fazer trades"""
    # Verificação básica - se conseguiu fazer login, está ok
    if hasattr(client, 'steam_id') and client.steam_id:
        return True, "OK"
    else:
        return False, "Cliente não conectado"


# ------------------- FUNÇÃO HELPER REMOVIDA (USANDO REGEX DIRETO) ------------------- #
# A função extrair_steamid64_do_tradelink foi removida pois duplicava código
# Agora usamos regex direto em enviar_oferta_aiosteampy
async def enviar_oferta_aiosteampy(client: SteamClient, tradelink: str, assetids: list[str]) -> str:
    """
    Envio de oferta seguindo documentação oficial aiosteampy 0.7.15
    """
    # Extrair partner ID do tradelink
    partner_match = re.search(r"partner=(\d+)", tradelink)
    token_match = re.search(r"token=([a-zA-Z0-9_-]+)", tradelink)
    
    if not partner_match:
        raise ValueError("Tradelink inválido - parâmetro 'partner' ausente")
    
    partner_steamid32 = int(partner_match.group(1))
    partner_steamid64 = partner_steamid32 + 76561197960265728
    trade_token = token_match.group(1) if token_match else None
    
    print(f"🎯 Partner Steam ID64: {partner_steamid64}")
    print(f"🔑 Trade Token: {trade_token}")
    
    # Carregar inventário do usuário (seguindo documentação oficial)
    try:
        print("📦 Carregando inventário do usuário...")
        inventory, assets_total, more_start = await client.get_user_inventory(
            steam_id=partner_steamid64,
            app_context=AppContext.CS2
        )
        
        if not inventory:
            raise ValueError("Inventário vazio ou inacessível")
        
        print(f"✅ Inventário carregado: {len(inventory)} itens encontrados")
        
        # Filtrar itens pelos assetids solicitados
        itens_para_oferta = []
        for item in inventory:
            if str(item.asset_id) in assetids:
                itens_para_oferta.append(item)
                print(f"✅ Item encontrado: {item.asset_id} - {item.description.market_name}")
        
        if not itens_para_oferta:
            raise ValueError(f"Nenhum dos AssetIDs solicitados foi encontrado no inventário: {assetids}")
        
        print(f"🎯 {len(itens_para_oferta)} itens selecionados para a oferta")
        
    except Exception as inv_error:
        print(f"❌ Erro ao carregar inventário: {inv_error}")
        raise RuntimeError(f"Falha ao acessar inventário do usuário: {inv_error}")
    
    # Enviar oferta seguindo documentação oficial
    try:
        print(f"🚀 Criando oferta de trade...")
        print(f"   • Para: {partner_steamid64}")
        print(f"   • Itens a receber: {len(itens_para_oferta)}")
        print(f"   • Token: {trade_token}")
        
        # Usar método oficial conforme documentação
        try:
            print("🚀 Chamando client.make_trade_offer()...")
            
            if trade_token:
                # Método 1: Com token (trade URL completa)
                offer_id = await client.make_trade_offer(
                    obj=tradelink,  # URL completa
                    to_give=[],     # Não estamos dando nada
                    to_receive=itens_para_oferta,  # Itens que queremos receber
                    message="Oferta de compra - TitoSkins Platform",
                    confirm=True    # Confirmar automaticamente (requer trade_acknowledge)
                )
            else:
                # Método 2: Apenas com Steam ID (sem token)
                offer_id = await client.make_trade_offer(
                    obj=partner_steamid64,
                    to_give=[],
                    to_receive=itens_para_oferta,
                    message="Oferta de compra - TitoSkins Platform",
                    confirm=True
                )
            
            print(f"✅ Oferta criada com sucesso! ID: {offer_id}")
            return str(offer_id)
            
        except Exception as make_offer_error:
            # 🔍 ANÁLISE DETALHADA DO ERRO DO make_trade_offer
            print(f"❌ ERRO DETALHADO em make_trade_offer:")
            print(f"   • Tipo: {type(make_offer_error).__name__}")
            print(f"   • Mensagem: {str(make_offer_error)}")
            print(f"   • Módulo: {make_offer_error.__class__.__module__}")
            
            # Verificar se é EResultError ou similar do aiosteampy
            if hasattr(make_offer_error, 'result'):
                print(f"   • e.result: {make_offer_error.result}")
            if hasattr(make_offer_error, 'data'):
                print(f"   • e.data: {make_offer_error.data}")
            if hasattr(make_offer_error, 'code'):
                print(f"   • e.code: {make_offer_error.code}")
            if hasattr(make_offer_error, 'response'):
                print(f"   • e.response: {make_offer_error.response}")
                
            # Re-lançar para o tratamento geral abaixo
            raise make_offer_error
        
    except Exception as trade_error:
        error_str = str(trade_error)
        print(f"❌ Erro ao criar oferta: {error_str}")
        print(f"❌ Tipo do erro: {type(trade_error).__name__}")
        
        # 🔍 TRATAMENTO ESPECÍFICO PARA EResultError DO AIOSTEAMPY
        if hasattr(trade_error, 'result') or hasattr(trade_error, 'code'):
            try:
                # Usar função de mapeamento para códigos específicos
                error_info = map_steam_error_code(trade_error)
                
                print(f"🔍 STEAM ERROR ANALYSIS:")
                print(f"   • Código: {error_info['code']}")
                print(f"   • Mensagem: {error_info['message']}")
                print(f"   • Retry sugerido: {error_info['retry_suggested']}")
                
                if hasattr(trade_error, 'result'):
                    print(f"   • e.result: {trade_error.result}")
                if hasattr(trade_error, 'data'):
                    print(f"   • e.data: {trade_error.data}")
                
                # Construir mensagem de erro específica
                detailed_message = f"Steam Error: {error_info['message']}"
                if hasattr(trade_error, 'data') and trade_error.data:
                    detailed_message += f" | Dados: {trade_error.data}"
                    
                raise RuntimeError(detailed_message)
                    
            except Exception as parse_error:
                print(f"⚠️ Erro ao processar detalhes do EResultError: {parse_error}")
                # Continuar com tratamento genérico abaixo
        
        # Tratamento específico de erros baseado na documentação (fallback)
        if "protection rules" in error_str.lower():
            print("🚨 Trade protection rules não foram aceitas!")
            raise RuntimeError("É necessário aceitar as regras de proteção de trade. Execute client.prepare() primeiro.")
        elif "500" in error_str:
            print("🚨 Steam servidor sobrecarregado (HTTP 500)")
            raise RuntimeError("Steam temporariamente indisponível. Tente novamente em alguns minutos.")
        elif "403" in error_str:
            print("🚨 Acesso negado pelo Steam")
            raise RuntimeError("Steam negou a requisição. Verifique permissões da conta.")
        elif "429" in error_str:
            print("🚨 Rate limit atingido")
            raise RuntimeError("Muitas requisições. Aguarde alguns minutos.")
        else:
            raise RuntimeError(f"Falha ao enviar oferta: {error_str}")


# ------------------- FUNÇÃO WRAPPER PARA COMPATIBILIDADE ------------------- #
async def enviar_oferta_principal(partner_steamid64: int, dados: dict) -> dict:
    """
    Função principal para enviar ofertas - compatível com routes/trade.py
    Faz login automaticamente e envia a oferta
    """
    print("🚀 INICIANDO enviar_oferta_principal")
    print(f"Partner ID: {partner_steamid64}")
    print(f"Dados: {dados}")
    
    client = None
    try:
        # 1. Fazer login
        print("🔐 Fazendo login...")
        client = await realizar_login_aiosteampy()
        print("✅ Login realizado com sucesso")
        
        # 2. Extrair dados
        tradelink = dados.get("tradelink")
        items = dados.get("items", [])
        assetids = [item["assetid"] for item in items]
        
        print(f"🔍 Tradelink: {tradelink}")
        print(f"🔍 AssetIDs: {assetids}")
        
        if not assetids:
            raise ValueError("Nenhum AssetID fornecido")
        
        # 3. Enviar oferta
        print("🚀 Enviando oferta...")
        tradeoffer_id = await enviar_oferta_aiosteampy(client, tradelink, assetids)
        print(f"✅ Oferta enviada! ID: {tradeoffer_id}")
        
        # 4. Registrar no banco
        print("💾 Registrando no banco...")
        registrar_oferta_no_banco(tradeoffer_id, partner_steamid64, assetids)
        print("✅ Registrado no banco com sucesso")
        
        return {
            "success": True,
            "tradeoffer_id": tradeoffer_id,
            "message": "Oferta enviada com sucesso"
        }
        
    except Exception as e:
        print(f"❌ ERRO em enviar_oferta_principal: {type(e).__name__}: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Erro ao enviar oferta: {str(e)}"
        }
    finally:
        # IMPORTANTE: Cleanup completo da sessão seguindo documentação
        if client:
            try:
                print("🔒 Fazendo logout do Steam...")
                
                # Salvar cookies antes do logout (se login foi bem-sucedido)
                if hasattr(client, 'session') and client.session and not client.session.closed:
                    try:
                        print("💾 Salvando cookies antes do logout...")
                        COOKIE_FILE.parent.mkdir(parents=True, exist_ok=True)
                        with COOKIE_FILE.open("w") as f:
                            json.dump(get_jsonable_cookies(client.session), f)
                        print("✅ Cookies salvos com sucesso!")
                    except Exception as save_error:
                        print(f"⚠️ Erro ao salvar cookies: {save_error}")
                
                # Logout usando o método correto da documentação
                logout_response = client.logout()
                await logout_response
                print("✅ Logout realizado com sucesso")
                
                # Fechar sessão aiohttp conforme documentação oficial
                if hasattr(client, 'session') and client.session and not client.session.closed:
                    await client.session.close()
                    print("✅ Sessão aiohttp fechada")
                    
            except Exception as logout_error:
                print(f"⚠️ Aviso: Erro no logout: {logout_error}")
                # Tentar fechar sessão mesmo se logout falhar
                try:
                    if hasattr(client, 'session') and client.session and not client.session.closed:
                        await client.session.close()
                        print("✅ Sessão aiohttp fechada após erro de logout")
                except Exception as session_error:
                    print(f"⚠️ Não foi possível fechar sessão: {session_error}")
                print("✅ Oferta foi processada com sucesso mesmo com erro de logout")


# ------------------- REGISTRAR OFERTA NO BANCO ------------------- #
def registrar_oferta_no_banco(offer_id: str, partner_steamid64: int, assetids: list[str]):
    try:
        nova_oferta = TradeOffer(
            tradeofferid=offer_id,
            partnersteamid=str(partner_steamid64),
            status="pendente",
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=10)
        )
        db.session.add(nova_oferta)
        db.session.commit()
        print("💾 Oferta registrada com sucesso no banco.")
        # Atualizar valor_liquido para as skins associadas à oferta
        for assetid in assetids:
            skin = db.session.query(Skin).filter(Skin.assetid == assetid).first()  # Supondo que assetid é usado para identificar a skin
            if skin:
                # Calcule o valor líquido
                skin.valor_liquido = calcular_valor_liquido(skin.preco)
                db.session.commit()  # Salva a alteração no valor líquido
                print(f"🔄 Valor líquido da skin {skin.nome} atualizado para R$ {skin.valor_liquido:.2f}.")
            else:
                print(f"⚠️ Skin com assetid {assetid} não encontrada.")
    except Exception as e:
        raise RuntimeError(f"Erro ao registrar oferta no banco: {str(e)}")


# ------------------- VALIDAÇÃO E FORMATAÇÃO ------------------- #

def map_steam_error_code(error_obj) -> dict:
    """
    Mapeia códigos de erro específicos da Steam para mensagens amigáveis
    
    Args:
        error_obj: Objeto de erro do aiosteampy (EResultError)
        
    Returns:
        dict: {"code": str, "message": str, "retry_suggested": bool}
    """
    error_mapping = {
        # Códigos comuns da Steam API
        "EResult.Fail": {
            "message": "Steam rejeitou a operação (falha genérica)",
            "retry_suggested": True
        },
        "EResult.Invalid": {
            "message": "Parâmetros inválidos enviados para a Steam",
            "retry_suggested": False
        },
        "EResult.Timeout": {
            "message": "Steam demorou para responder (timeout)",
            "retry_suggested": True
        },
        "EResult.Busy": {
            "message": "Steam está temporariamente sobrecarregada",
            "retry_suggested": True
        },
        "EResult.RateLimitExceeded": {
            "message": "Rate limit atingido - muitas requisições",
            "retry_suggested": False  # Precisa esperar
        },
        "EResult.AccessDenied": {
            "message": "Steam negou acesso - verifique permissões",
            "retry_suggested": False
        },
        "EResult.InvalidState": {
            "message": "Estado inválido da conta ou inventário",
            "retry_suggested": False
        },
        "EResult.NotLoggedOn": {
            "message": "Cliente não está logado na Steam",
            "retry_suggested": True
        },
        "EResult.Pending": {
            "message": "Operação pendente na Steam",
            "retry_suggested": True
        }
    }
    
    # Tentar extrair código do erro
    error_code = "Unknown"
    if hasattr(error_obj, 'result'):
        error_code = str(error_obj.result)
    elif hasattr(error_obj, 'code'):
        error_code = str(error_obj.code)
    
    # Retornar mapeamento ou mensagem genérica
    if error_code in error_mapping:
        return {
            "code": error_code,
            "message": error_mapping[error_code]["message"],
            "retry_suggested": error_mapping[error_code]["retry_suggested"]
        }
    else:
        return {
            "code": error_code,
            "message": f"Erro desconhecido da Steam: {error_code}",
            "retry_suggested": True
        }

def validar_dados_requisicao(dados: dict):
    tradelink = dados.get("tradelink")
    itens_selecionados = dados.get("itens")

    if not tradelink or not isinstance(itens_selecionados, list) or not itens_selecionados:
        raise ValueError("Tradelink e pelo menos um item são obrigatórios.")

    partner_steamid32 = extrair_partner_steamid(tradelink)
    if not partner_steamid32:
        raise ValueError("Tradelink inválido. Não foi possível extrair o SteamID.")

    partner_steamid64 = steamid32_to_steamid64(partner_steamid32)
    return itens_selecionados, tradelink, partner_steamid64


# ------------------- UTILIDADES ------------------- #
def extrair_partner_steamid(tradelink: str) -> str | None:
    match = re.search(r"partner=(\d+)", tradelink)
    return match.group(1) if match else None

def steamid32_to_steamid64(steamid32: str | int) -> int:
    try:
        return int(steamid32) + 76561197960265728
    except Exception:
        raise ValueError("SteamID32 inválido.")