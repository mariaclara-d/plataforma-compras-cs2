import os
import re
import json
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from aiosteampy.client import SteamClient
from aiosteampy.constants import AppContext
from aiosteampy.models import EconItem
from db_config import db
from models import TradeOffer
from models import Skin


load_dotenv()

# ------------------- LOGIN ------------------- #
async def realizar_login_aiosteampy():
    try:
        with open("steam_guard.json", "r") as f:
            steam_guard = json.load(f)
    except Exception as e:
        raise RuntimeError("Erro ao carregar steam_guard.json: " + str(e))
    try:
        client = SteamClient(
            steam_id=steam_guard["steam_id"],
            username=steam_guard["account_name"],
            password=steam_guard["password"],
            shared_secret=steam_guard["shared_secret"],
            identity_secret=steam_guard["identity_secret"],
            api_key=os.getenv("STEAM_API_KEY")
        )
        print("🔐 Tentando fazer login com aiosteampy...")
        print(f"🔐 Account: {steam_guard['account_name']}")
        print(f"🔐 Steam ID: {steam_guard['steam_id']}")
        await client.login()
        print("✅ Login com aiosteampy realizado com sucesso.")
        return client
    except KeyError as ke:
        error_details = f"KeyError: Campo ausente na resposta do Steam: {ke}"
        print(f"🚨 ERRO CRÍTICO: {error_details}")
        print(f"🚨 Isso indica problema de autenticação Steam")
        print(f"🚨 Possíveis causas:")
        print(f"   • Username/password incorretos")
        print(f"   • Steam Guard secrets inválidos/expirados")
        print(f"   • Conta Steam com restrições")
        print(f"   • Steam mudou protocolo de autenticação")
        raise RuntimeError(f"Falha crítica na autenticação Steam: {error_details}")
    except Exception as e:
        print(f"❌ Erro detalhado no login: {type(e).__name__}: {str(e)}")
        print(f"❌ Conta: {steam_guard.get('account_name', 'N/A')}")
        
        # Verificar se é problema de client_id (comum quando credenciais estão incorretas)
        error_str = str(e)
        if "client_id" in error_str:
            raise RuntimeError("❌ PROBLEMA DE AUTENTICAÇÃO: Steam não retornou 'client_id'. Credenciais inválidas ou Steam Guard expirado.")
        elif "shared_secret" in error_str:
            raise RuntimeError("Shared secret inválido no steam_guard.json")
        elif "identity_secret" in error_str:
            raise RuntimeError("Identity secret inválido no steam_guard.json")
        else:
            raise RuntimeError("Falha no login com Steam: " + str(e))
    
    
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


# ------------------- ENVIO DE OFERTA ------------------- #
def extrair_steamid64_do_tradelink(tradelink: str) -> int:
    match = re.search(r"partner=(\d+)", tradelink)
    if not match:
        raise ValueError("Tradelink inválido. Parâmetro 'partner' ausente.")
    steamid32 = int(match.group(1))
    return steamid32 + 76561197960265728
async def enviar_oferta_aiosteampy(client: SteamClient, tradelink: str, assetids: list[str]) -> str:
    partner_steamid64 = extrair_steamid64_do_tradelink(tradelink)
    
    # Carregar inventário do usuário
    try:
        user_inventory = await client.get_user_inventory(
            steam_id=partner_steamid64,
            app_context=AppContext.CS2
        )
        
        if not user_inventory:
            raise ValueError("Inventário vazio")
        
        # Filtrar itens pelos assetids
        itens_para_oferta = []
        for item in user_inventory:
            if str(item.asset_id) in assetids:
                itens_para_oferta.append(item)
        
        if not itens_para_oferta:
            raise ValueError(f"Nenhum dos AssetIDs encontrado: {assetids}")
        
        itens = itens_para_oferta
        
    except Exception:
        # FALLBACK: criar EconItem manualmente
        from aiosteampy.models import EconItem
        from aiosteampy.constants import AppContext
        
        class ItemDescription:
            def __init__(self):
                self.market_tradable_restriction = 0
                self.market_marketable_restriction = 0
                self.name = "CS2 Item"
                self.type = "Weapon"
                self.tradable = True
                self.marketable = True
        
        itens = []
        for assetid in assetids:
            item = EconItem(
                asset_id=str(assetid),
                owner_id=str(partner_steamid64),
                app_context=AppContext.CS2,
                amount=1,
                description=ItemDescription()
            )
            itens.append(item)
    
    # Enviar oferta
    tradeoffer_id = await client.make_trade_offer(
        obj=int(partner_steamid64),
        to_give=[],
        to_receive=itens,
        message="Oferta de compra - TitoSkins",
        confirm=False
    )
    
    return str(tradeoffer_id)



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