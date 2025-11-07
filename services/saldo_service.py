from db_config import db
from models import TradeOffer, Skin, Transacao
from sqlalchemy import func
from decimal import Decimal

def calcular_saldo_usuario(steamid, percentual_comissao=0.65):
    """
    Calcula o saldo disponível do usuário baseado nas skins vendidas
    e descontando transações já pagas.

    :param steamid: SteamID64 do usuário
    :param percentual_comissao: percentual que o usuário recebe (ex: 0.65 = 65%)
    :return: saldo (float)
    """

    total_vendido = (
        db.session.query(func.coalesce(func.sum(Skin.preco), 0.0))
        .join(TradeOffer, TradeOffer.tradeofferid == Skin.tradeofferid)
        .filter(TradeOffer.partnersteamid == steamid)
        .filter(TradeOffer.status == "aceito")
        .scalar()
    )

    # Converter para Decimal para evitar erro de tipos
    total_vendido = Decimal(str(total_vendido)) if total_vendido else Decimal('0.0')
    percentual_comissao = Decimal(str(percentual_comissao))

    total_para_usuario = total_vendido * percentual_comissao

    total_pago = (
        db.session.query(func.coalesce(func.sum(Transacao.valor), 0.0))
        .filter(Transacao.steamid == steamid)
        .filter(Transacao.status == "pago")
        .scalar()
    )

    # Converter total_pago para Decimal
    total_pago = Decimal(str(total_pago)) if total_pago else Decimal('0.0')

    saldo_atual = total_para_usuario - total_pago
    return float(max(saldo_atual, Decimal('0.0')))
