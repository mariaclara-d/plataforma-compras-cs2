from db_config import db
from models import TradeOffer, Skin, Transacao
from sqlalchemy import func

def calcular_saldo_usuario(steamid, percentual_comissao=0.8):
    """
    Calcula o saldo disponível do usuário baseado nas skins vendidas
    e descontando transações já pagas.

    :param steamid: SteamID64 do usuário
    :param percentual_comissao: percentual que o usuário recebe (ex: 0.65 = 80%)
    :return: saldo (float)
    """

    total_vendido = (
        db.session.query(func.coalesce(func.sum(Skin.preco), 0.0))
        .join(TradeOffer, TradeOffer.tradeofferid == Skin.tradeofferid)
        .filter(TradeOffer.partnersteamid == steamid)
        .filter(TradeOffer.status == "aceito")
        .scalar()
    )

    total_para_usuario = total_vendido * percentual_comissao

    total_pago = (
        db.session.query(func.coalesce(func.sum(Transacao.valor), 0.0))
        .filter(Transacao.steamid == steamid)
        .filter(Transacao.status == "pago")
        .scalar()
    )

    saldo_atual = total_para_usuario - total_pago
    return max(saldo_atual, 0.0)
