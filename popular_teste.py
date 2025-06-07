from app import create_app
from db_config import db
from models.skins import Skin
from models.trade_offers import TradeOffer
from models.transacoes import Transacao
from datetime import datetime, timedelta, timezone

def popular_dados_teste(steamid):
    # Cria um trade_offer aceito
    agora = datetime.now(timezone.utc)
    trade_offer = TradeOffer(
        tradeofferid='TST123',
        partnersteamid=steamid,
        status='aceito',
        created_at=agora,
        updated_at=agora,
        expires_at=agora + timedelta(days=7)
    )
    db.session.add(trade_offer)
    db.session.commit()

    # Cria uma skin vendida vinculada ao trade_offer
    skin = Skin(
        nome='AK-47 | Redline',
        preco=100.0,
        valor_liquido=65.0,
        raridade='Classified',
        descricao='Skin de teste',
        assetid='ASSET123',
        tradeofferid='TST123'
    )
    db.session.add(skin)
    db.session.commit()

    # Cria uma transação paga (opcional, para testar saldo descontado)
    transacao = Transacao(
        steamid=steamid,
        valor=20.0,
        metodo='pix',
        status='pago'
    )
    db.session.add(transacao)
    db.session.commit()

    print(f"Dados de teste criados para steamid {steamid}.")

if __name__ == "__main__":
    steamid = "12345678901234567"  # Use o mesmo do teste do endpoint
    app = create_app()
    with app.app_context():
        popular_dados_teste(steamid)
