import os
import re
import json
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from aiosteampy.client import SteamClient
from aiosteampy.constants import AppContext
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
        await client.login()
        print("✅ Login com aiosteampy realizado com sucesso.")
        return client
    except Exception as e:
        raise RuntimeError("Falha no login com Steam: " + str(e))
    
    
    # ------------------- VALOR LÍQUIDO------------------- #
    
def calcular_valor_liquido(preco, percentual_comissao=0.65):
    """Calcula o valor líquido baseado no preço e percentual de comissão."""
    if preco is None:
        return None
    return preco * percentual_comissao



# ------------------- ENVIO DE OFERTA ------------------- #
def extrair_steamid64_do_tradelink(tradelink: str) -> int:
    match = re.search(r"partner=(\d+)", tradelink)
    if not match:
        raise ValueError("Tradelink inválido. Parâmetro 'partner' ausente.")
    steamid32 = int(match.group(1))
    return steamid32 + 76561197960265728
async def enviar_oferta_aiosteampy(client: SteamClient, tradelink: str, assetids: list[str]) -> str:
    partner_steamid64 = extrair_steamid64_do_tradelink(tradelink)
    print(f"🎒 Buscando itens do inventário de {partner_steamid64}...")
    itens = []
    
    # Buscar itens do inventário
    for assetid in assetids:
        try:
            item = await client.get_user_inventory_item(
                steam_id=partner_steamid64,
                app_context=AppContext.CS2,
                obj=int(assetid)
            )
            if not item:
                raise Exception(f"Item com assetid {assetid} não encontrado no inventário do parceiro.")
            itens.append(item)
        except Exception as e:
            raise RuntimeError(f"Erro ao buscar o item {assetid}: {str(e)}")
    
    # Enviar oferta de troca
    try:
        print("🚀 Enviando oferta de troca...")
        tradeoffer_id = await client.make_trade_offer(
            obj=tradelink,
            to_give=[],
            to_receive=itens,
            message="Oferta enviada pelo site"
        )
        print(f"🎉 Oferta enviada com sucesso! ID: {tradeoffer_id}")
        
        # Registrar a oferta no banco, passando os assetids
        registrar_oferta_no_banco(tradeoffer_id, partner_steamid64, assetids)
        
        return str(tradeoffer_id)
    except Exception as e:
        raise RuntimeError(f"Erro ao enviar a oferta: {str(e)}")



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