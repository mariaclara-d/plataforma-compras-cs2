# services/aiosteampy_service.py

import os
import re
import json
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from aiosteampy.client import SteamClient
from aiosteampy.constants import AppContext
from db_config import db
from models import TradeOffer

load_dotenv()

# ------------------- LOGIN ------------------- #
async def realizar_login_aiosteampy():
    with open("steam_guard.json", "r") as f:
        steam_guard = json.load(f)

    client = SteamClient(
        steam_id=steam_guard["steam_id"],
        username=steam_guard["account_name"],
        password=steam_guard["password"],
        shared_secret=steam_guard["shared_secret"],
        identity_secret=steam_guard["identity_secret"],
        api_key=os.getenv("STEAM_API_KEY")
    )

    await client.login()
    print("✅ Login feito.")
    return client

# ------------------- ENVIO DE OFERTA ------------------- #
def extrair_steamid64_do_tradelink(tradelink: str) -> int:
    match = re.search(r"partner=(\d+)", tradelink)
    if not match:
        raise ValueError("Tradelink inválido")
    steamid32 = int(match.group(1))
    return steamid32 + 76561197960265728

async def enviar_oferta_aiosteampy(client, tradelink, assetids: list):
    print("🎒 Buscando itens do inventário do parceiro...")

    partner_steamid64 = extrair_steamid64_do_tradelink(tradelink)
    itens = []
    for assetid in assetids:
        item = await client.get_user_inventory_item(
            steam_id=partner_steamid64,
            app_context=AppContext.CS2,
            obj=int(assetid)
        )
        if not item:
            raise Exception(f"Item com assetid {assetid} não encontrado.")
        itens.append(item)

    print("🚀 Enviando oferta de troca...")
    tradeoffer_id = await client.make_trade_offer(
        obj=tradelink,
        to_give=[],
        to_receive=itens,
        message="Oferta enviada pelo site"
    )

    print(f"🎉 Oferta enviada com sucesso! ID: {tradeoffer_id}")
    return str(tradeoffer_id)
# ------------------- REGISTRAR OFERTA NO BANCO ------------------- #
def registrar_oferta_no_banco(offer_id: str, partner_steamid64: int):
    nova_oferta = TradeOffer(
        tradeofferid=str(offer_id),
        partnersteamid=str(partner_steamid64),
        status="pendente",
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=10)
    )
    db.session.add(nova_oferta)
    db.session.commit()
    print("💾 Oferta registrada no banco.")

# ------------------- VALIDAÇÃO E FORMATAÇÃO ------------------- #
def validar_dados_requisicao(dados):
    tradelink = dados.get("tradelink")
    itens_selecionados = dados.get("itens")

    if not tradelink or not itens_selecionados:
        raise ValueError("Tradelink e itens são obrigatórios.")

    partner_steamid32 = extrair_partner_steamid(tradelink)
    if not partner_steamid32:
        raise ValueError("Tradelink inválido.")

    partner_steamid64 = steamid32_to_steamid64(partner_steamid32)

    return itens_selecionados, tradelink, partner_steamid64

def formatar_itens_recebidos(itens):
    itens_formatados = []
    for item in itens:
        if "assetid" not in item:
            raise ValueError("Item sem assetid recebido!")
        itens_formatados.append({
            "appid": item.get("appid", "730"),
            "contextid": item.get("contextid", "2"),
            "assetid": item["assetid"]
        })
    return itens_formatados

# ------------------- UTILIDADES ------------------- #
def extrair_partner_steamid(tradelink):
    match = re.search(r"partner=(\d+)", tradelink)
    return match.group(1) if match else None

def steamid32_to_steamid64(steamid32):
    try:
        return int(steamid32) + 76561197960265728
    except ValueError:
        raise ValueError("SteamID32 inválido.")
