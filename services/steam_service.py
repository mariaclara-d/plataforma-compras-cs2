import os
import re
import base64
import hmac
import hashlib
import time 
from datetime import datetime, timedelta, timezone
from steampy.client import SteamClient
from steampy.models import Asset, GameOptions
from dotenv import load_dotenv
from db_config import db
from models import TradeOffer

load_dotenv()


def realizar_login_steam():
    username = os.getenv("STEAM_USERNAME")
    password = os.getenv("STEAM_PASSWORD")
    shared_secret = os.getenv("STEAM_SHARED_SECRET")
    identity_secret = os.getenv("STEAM_IDENTITY_SECRET")
    steam_api_key = os.getenv("STEAM_API_KEY")
    steam_guard= os.getenv("STEAM_GUARD_FILE")

    if not all([username, password, shared_secret, identity_secret, steam_api_key]):
        raise Exception("Credenciais da Steam ausentes ou inválidas")

    steam_client = SteamClient(steam_api_key)

    try:
        steam_client.login(username, password, steam_guard)
        print("Login com Steampy realizado com sucesso.")
    except Exception as e:
        print("Erro durante o login com Steampy:", e)
        raise Exception(f"Falha ao logar com Steampy: {e}")

    if not steam_client.is_session_alive():
        raise Exception("Login falhou ou sessão está inativa")

    steam_client.set_identity_secret(identity_secret)
    return steam_client



def validar_dados_requisicao(dados):
    tradelink = dados.get("tradelink")
    itens_selecionados = dados.get("itens")

    if not tradelink or not itens_selecionados:
        raise ValueError("Tradelink e itens são obrigatórios")

    partner_steamid32 = extrair_partner_steamid(tradelink)
    if not partner_steamid32:
        raise ValueError("Tradelink inválido")

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




def criar_oferta(steam_client, itens, tradelink):
    assets = [Asset(item["appid"], item["contextid"], item["assetid"]) for item in itens]
    
    return steam_client.make_offer_with_url(
        items_from_me=[],
        items_from_them=assets,
        trade_offer_url=tradelink,
        message="Oferta enviada pelo site!"
    )



def registrar_oferta_no_banco(offer_id, steamid64):
    nova_oferta = TradeOffer(
        offer_id=offer_id,
        steamid=steamid64,
        status="pendente",
        data_criacao=datetime.now(timezone.utc),
        data_expiracao=datetime.now(timezone.utc) + timedelta(minutes=10)
    )
    db.session.add(nova_oferta)
    db.session.commit()


def extrair_partner_steamid(tradelink):
    match = re.search(r"partner=(\d+)", tradelink)
    return match.group(1) if match else None


def steamid32_to_steamid64(steamid32):
    try:
        return int(steamid32) + 76561197960265728
    except ValueError:
        raise ValueError("SteamID32 inválido")

