# services/steam_utils.py

import re
from datetime import datetime, timedelta, timezone
from db_config import db
from models import TradeOffer

def extrair_partner_steamid(tradelink):
    """Extrai partner ID do tradelink"""
    if not tradelink or "partner=" not in tradelink:
        return None
    match = re.search(r"partner=(\d+)", tradelink)
    return match.group(1) if match else None

def extrair_token_tradelink(tradelink):
    """Extrai token do tradelink"""
    match = re.search(r"token=([^&]+)", tradelink)
    return match.group(1) if match else None

def steamid32_to_steamid64(steamid32):
    """Converte SteamID32 para SteamID64"""
    if steamid32 is None or not str(steamid32).isdigit():
        raise ValueError(f"SteamID32 inválido: {steamid32}")
    return int(steamid32) + 76561197960265728

def validar_dados_requisicao(dados):
    """Valida dados da requisição de trade"""
    tradelink = dados.get("tradelink")
    itens_selecionados = dados.get("itens")

    if not tradelink or not itens_selecionados:
        raise ValueError("Tradelink e itens são obrigatórios")

    partner_steamid32 = extrair_partner_steamid(tradelink)
    if not partner_steamid32:
        raise ValueError("Tradelink inválido")

    partner_steamid64 = steamid32_to_steamid64(partner_steamid32)
    return itens_selecionados, tradelink, partner_steamid64

def registrar_oferta_no_banco(offer_id, steamid64):
    """Registra oferta no banco de dados"""
    nova_oferta = TradeOffer(
        offer_id=offer_id,
        steamid=steamid64,
        status="pendente",
        data_criacao=datetime.now(timezone.utc),
        data_expiracao=datetime.now(timezone.utc) + timedelta(minutes=10)
    )
    db.session.add(nova_oferta)
    db.session.commit()

def calcular_valor_liquido(preco, percentual_comissao=0.65):
    """
    Calcula valor líquido após comissão
    Consolidada aqui para evitar duplicação
    """
    if preco is None:
        return 0.0
    try:
        return round(float(preco) * percentual_comissao, 2)
    except (ValueError, TypeError):
        return 0.0
