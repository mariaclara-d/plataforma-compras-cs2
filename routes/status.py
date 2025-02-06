import time
import os
from db_config import db
from datetime import datetime, timezone  # Importação correta
from steampy.client import SteamClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import TradeOffer  # Importe o modelo TradeOffer

# Configurações do Steam
STEAM_API_KEY = os.getenv("STEAM_API_KEY")
STEAM_USERNAME = os.getenv("STEAM_USERNAME")
STEAM_PASSWORD = os.getenv("STEAM_PASSWORD")
STEAM_GUARD_PATH = "./steam_guard.json"

# Configurações do banco de dados
SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI")  # Substitua pelo seu URI de conexão
engine = create_engine(SQLALCHEMY_DATABASE_URI)
Session = sessionmaker(bind=engine)

def verificar_status_ofertas():
    # Conecta ao Steam
    steam_client = SteamClient(STEAM_API_KEY)
    steam_client.login(STEAM_USERNAME, STEAM_PASSWORD, STEAM_GUARD_PATH)

    while True:
        try:
            # Utilize o db.session do Flask-SQLAlchemy
            pendentes = db.session.query(TradeOffer).filter(TradeOffer.status == 'pendente').all()

            for oferta in pendentes:
                try:
                    print(f"Verificando oferta {oferta.tradeofferid}...")
                    # Converta oferta.expires_at para aware assumindo UTC:
                    expires_at_aware = oferta.expires_at.replace(tzinfo=timezone.utc)
                    agora = datetime.now(timezone.utc)
                    print(f"expires_at: {expires_at_aware}, agora: {agora}")
                    
                    offer_status = steam_client.get_trade_offer(oferta.tradeofferid, merge=False, use_webtoken=True)
                    print(f"Resposta da API para oferta {oferta.tradeofferid}: {offer_status}")
                    
                    # Se a resposta da API estiver vazia ou não contiver 'trade_offer_state'
                    
                    novo_status = offer_status['trade_offer_state']
                    status_map = {
                        1: 'pendente',  # Pendente
                        2: 'aceito',    # Aceita
                        3: 'cancelado', # Cancelada
                    }
                    novo_status_str = status_map.get(novo_status, 'desconhecido')

                    # Atualiza o status conforme retorno da API
                    oferta.status = novo_status_str
                    if novo_status_str == 'cancelado':
                        oferta.cancelado_por='usuario'
                    else:
                        oferta.cancelado_por = None
                        
                    oferta.updated_at = datetime.now(timezone.utc)
                    db.session.commit()
                    print(f"Oferta {oferta.tradeofferid} atualizada para {novo_status_str} via API.")

                    # Se a oferta ainda está pendente mas já expirou, cancelar automaticamente
                    if novo_status_str == 'pendente' and agora > expires_at_aware:
                        print(f"Cancelando oferta {oferta.tradeofferid} por expiração...")
                        steam_client.cancel_trade_offer(oferta.tradeofferid)
                        oferta.status = 'cancelado'
                        oferta.cancelado_por='site'
                        
                        oferta.updated_at = datetime.now(timezone.utc)
                        db.session.commit()
                        print(f"Oferta {oferta.tradeofferid} cancelada.")

                except Exception as e:
                    print(f"Erro ao verificar oferta {oferta.tradeofferid}: {e}")

        except Exception as e:
            print(f"Erro no loop de verificação: {e}")

        # Espera 1 minuto antes de verificar novamente
        time.sleep(60)

# Inicia o serviço de acompanhamento
if __name__ == "__main__":
    from app import create_app
    app = create_app()
    
    with app.app_context():
        verificar_status_ofertas()