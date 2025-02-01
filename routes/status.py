import time
import os
from datetime import datetime, timedelta  # Importação correta
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

# Função para verificar e atualizar o status das ofertas
def verificar_status_ofertas():
    # Conecta ao Steam
    steam_client = SteamClient(STEAM_API_KEY)
    try:
        steam_client.login(STEAM_USERNAME, STEAM_PASSWORD, STEAM_GUARD_PATH)
        print("Login na Steam realizado com sucesso!")
    except Exception as e:
        print(f"Erro ao fazer login na Steam: {e}")
        return

    while True:
        try:
            # Cria uma sessão do banco de dados
            session = Session()

            # Obtém ofertas pendentes do banco de dado
            pendentes = session.query(TradeOffer).filter(TradeOffer.status == 'pendente').all()

            for oferta in pendentes:
                try:
                    # Verifica o status da oferta no Steam
                    offer_status = steam_client.get_trade_offer(oferta.tradeofferid)
                    print(f"Resposta da API para oferta {oferta.tradeofferid}: {offer_status}")

                    if not offer_status.get('response'):
                        print(f"Oferta {oferta.tradeofferid} não encontrada ou resposta inválida.")
                        continue  # Pula para a próxima oferta

                    trade_offer = offer_status['response'].get('offer')
                    if not trade_offer:
                        print(f"Oferta {oferta.tradeofferid} não encontrada ou resposta inválida.")
                        continue  # Pula para a próxima oferta

                    novo_status = trade_offer['trade_offer_state']

                    # Mapeia o status da Steam para o status no banco de dados
                    status_map = {
                        1: 'pendente',  # Pendente
                        2: 'aceito',    # Aceita
                        3: 'cancelado', # Cancelada
                    }
                    novo_status_str = status_map.get(novo_status, 'desconhecido')

                    # Atualiza o status no banco de dados
                    oferta.status = novo_status_str
                    oferta.updated_at = datetime.now()
                    session.commit()

                    # Se a oferta estiver pendente há mais de 10 minutos, cancela
                    if novo_status_str == 'pendente' and datetime.now() > oferta.expires_at:
                        print(f"Cancelando oferta {oferta.tradeofferid}...")
                        steam_client.cancel_trade_offer(oferta.tradeofferid)
                        oferta.status = 'cancelado'
                        oferta.updated_at = datetime.now()
                        session.commit()
                        print(f"Oferta {oferta.tradeofferid} cancelada.")

                except Exception as e:
                    print(f"Erro ao verificar oferta {oferta.tradeofferid}: {e}")

            # Fecha a sessão do banco de dados
            session.close()

        except Exception as e:
            print(f"Erro no loop de verificação: {e}")

        # Espera 1 minuto antes de verificar novamente
        time.sleep(60)

# Inicia o serviço de acompanhamento
if __name__ == "__main__":
    verificar_status_ofertas()