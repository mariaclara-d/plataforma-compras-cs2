# services/steam_utils.py

import re
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
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

def calcular_valor_liquido(preco, percentual_comissao=0.65):
    """
    Calcula valor líquido após comissão
    Consolidada aqui para evitar duplicação
    """
    if preco is None:
        return Decimal('0.00')
    try:
        # Converter para Decimal para manter precisão financeira
        preco_decimal = Decimal(str(preco))
        comissao_decimal = Decimal(str(percentual_comissao))
        resultado = preco_decimal * comissao_decimal
        # Arredondar para 2 casas decimais
        return resultado.quantize(Decimal('0.01'))
    except (ValueError, TypeError, InvalidOperation):
        return Decimal('0.00')
