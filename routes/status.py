import asyncio
import os
import json
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from aiosteampy.client import SteamClient
from aiosteampy.constants import TradeOfferStatus
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask
from models import TradeOffer, Skin, Saldo
from sqlalchemy.exc import SQLAlchemyError

load_dotenv()

# Banco de dados
DATABASE_URL = os.getenv("SQLALCHEMY_DATABASE_URI")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

# Steam
STEAM_API_KEY = os.getenv("STEAM_API_KEY")
STEAM_GUARD_FILE = os.getenv("STEAM_GUARD_FILE")

# Logging
logging.basicConfig(
    filename='status_ofertas.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s'
)

STATUS_MAP = {
    TradeOfferStatus.INVALID: 'inválido',
    TradeOfferStatus.ACTIVE: 'pendente',
    TradeOfferStatus.ACCEPTED: 'aceito',
    TradeOfferStatus.COUNTERED: 'contra-ofertada',
    TradeOfferStatus.EXPIRED: 'expirada',
    TradeOfferStatus.CANCELED: 'cancelado',
    TradeOfferStatus.DECLINED: 'recusada',
    TradeOfferStatus.INVALID_ITEMS: 'itens inválidos',
    TradeOfferStatus.CONFIRMATION_NEED: 'precisa de confirmação',
    TradeOfferStatus.CANCELED_BY_SECONDARY_FACTOR: 'cancelado',
    TradeOfferStatus.STATE_IN_ESCROW: 'em custódia',
}

async def login_aiosteampy():
    if not STEAM_GUARD_FILE or not os.path.exists(STEAM_GUARD_FILE):
        logging.error("Arquivo de guardas do Steam não encontrado.")
        raise FileNotFoundError("Arquivo de guardas do Steam não encontrado.")
    try:
        with open(STEAM_GUARD_FILE, 'r') as f:
            guard = json.load(f)
        client = SteamClient(
            steam_id=guard["steam_id"],
            username=guard["account_name"],
            password=guard["password"],
            shared_secret=guard["shared_secret"],
            identity_secret=guard["identity_secret"],
            api_key=STEAM_API_KEY
        )
        await client.login()
        logging.info(" Login efetuado com sucesso.")
        return client
    except Exception as e:
        logging.error(f"Erro ao fazer login no Steam: {e}")
        raise

def calcular_valor_liquido(preco, percentual_comissao=None):
    """Calcula o valor líquido baseado no preço e percentual de comissão."""
    if percentual_comissao is None:
        percentual_comissao = Decimal(os.getenv("PERCENTUAL_COMISSAO", "0.65"))
    if preco is None:
        return None
    return preco * percentual_comissao

async def verificar_status():
    session = Session()
    agora = datetime.now(timezone.utc)
    try:
        client = await login_aiosteampy()
        pendentes = session.query(TradeOffer).filter(TradeOffer.status == 'pendente').all()
        logging.info(f" {len(pendentes)} ofertas pendentes encontradas.")
        for oferta in pendentes:
            try:
                logging.info(f" Verificando oferta {oferta.tradeofferid}...")
                trade = await client.get_trade_offer(int(oferta.tradeofferid))
                status_str = STATUS_MAP.get(trade.status, 'desconhecido')
                oferta.status = status_str
                oferta.updated_at = agora
                oferta.cancelado_por = 'usuario' if status_str in ['cancelado', 'recusada'] else None

                # Atualizar saldo e valor líquido se a oferta for aceita
                if status_str == 'aceito':
                    skin = session.query(Skin).filter(Skin.tradeofferid == oferta.tradeofferid).first()
                    if skin:
                        skin.valor_liquido = calcular_valor_liquido(skin.preco)
                        logging.info(f" Valor líquido da skin {skin.nome} atualizado para R$ {skin.valor_liquido:.2f}.")
                        saldo = session.query(Saldo).filter(Saldo.steamid == oferta.partnersteamid).first()
                        if saldo:
                            saldo.valor += skin.valor_liquido
                        else:
                            saldo = Saldo(steamid=oferta.partnersteamid, valor=skin.valor_liquido)
                            session.add(saldo)
                        session.commit()
                        logging.info(f" Saldo do usuário {oferta.partnersteamid} atualizado para R$ {saldo.valor:.2f}.")
                    else:
                        logging.warning(f"Nenhuma skin encontrada para a oferta {oferta.tradeofferid}.")

                session.commit()
                logging.info(f" Status atualizado: {oferta.tradeofferid} → {status_str}")

                if status_str == 'pendente' and agora > oferta.expires_at:
                    await client.cancel_trade_offer(int(oferta.tradeofferid))
                    oferta.status = 'cancelado'
                    oferta.cancelado_por = 'site'
                    oferta.updated_at = agora
                    session.commit()
                    logging.info(f"⏱ Oferta expirada cancelada: {oferta.tradeofferid}")
            except SQLAlchemyError as db_err:
                session.rollback()
                logging.error(f" Erro de banco verificando oferta {oferta.tradeofferid}: {db_err}")
            except Exception as e:
                session.rollback()
                logging.error(f" Erro verificando oferta {oferta.tradeofferid}: {e}")
    except Exception as e:
        logging.error(f" Erro na execução geral: {e}")
    finally:
        session.close()

# Flask + APScheduler
app = Flask(__name__)
scheduler = BackgroundScheduler()

@scheduler.scheduled_job('interval', seconds=60)
def tarefa_agendada():
    logging.info("Executando tarefa agendada de verificação de ofertas...")
    asyncio.run(verificar_status())

scheduler.start()

@app.route("/")
def index():
    return "Tarefa agendada de verificação de ofertas está rodando!"

if __name__ == '__main__':
    app.run(debug=True)