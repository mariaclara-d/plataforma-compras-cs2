import time
import os
from db_config import db
from datetime import datetime, timezone  # Importação correta
from steampy import SteamClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import TradeOffer  # Importe o modelo TradeOffer
from requests.exceptions import ConnectionError
from urllib.parse import unquote

# Configurações do Steam
STEAM_API_KEY = os.getenv("STEAM_API_KEY")
STEAM_USERNAME = os.getenv("STEAM_USERNAME")
STEAM_PASSWORD = os.getenv("STEAM_PASSWORD")
STEAM_GUARD_PATH = "./steam_guard.json"

# Configurações do banco de dados

SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI")
engine = create_engine(SQLALCHEMY_DATABASE_URI)
Session = sessionmaker(bind=engine)

def login_with_retry(steam_client, username, password, steam_guard_path, retries=3, delay=5):
    attempt = 0
    while attempt < retries:
        try:
            steam_client.login(username, password, steam_guard_path)
            print("Login realizado com sucesso!")
            # Extração do access token:
            steam_login_secure_cookies = [cookie for cookie in steam_client._session.cookies if cookie.name == 'steamLoginSecure']
            if steam_login_secure_cookies:
                cookie_value = steam_login_secure_cookies[0].value
                decoded_cookie_value = unquote(cookie_value)
                access_token_parts = decoded_cookie_value.split('||')
                if len(access_token_parts) >= 2:
                    steam_client._access_token = access_token_parts[1]
                else:
                    print("Access token não encontrado no cookie steamLoginSecure")
            else:
                print("Cookie steamLoginSecure não encontrado")
            return True
        except ConnectionError as e:
            attempt += 1
            print(f"Erro na tentativa de login ({attempt}/{retries}): {e}")
            time.sleep(delay)
    return False

def verificar_status_ofertas():
    # Configura o SteamClient e a sessão com retry se desejar
    steam_client = SteamClient(STEAM_API_KEY)
    if not login_with_retry(steam_client, STEAM_USERNAME, STEAM_PASSWORD, STEAM_GUARD_PATH):
        print("Falha ao realizar login após várias tentativas.")
        return

    while True:
        try:
            pendentes = db.session.query(TradeOffer).filter(TradeOffer.status == 'pendente').all()
            for oferta in pendentes:
                try:
                    print(f"Verificando oferta {oferta.tradeofferid}...")
                    expires_at_aware = oferta.expires_at.replace(tzinfo=timezone.utc)
                    agora = datetime.now(timezone.utc)
                    print(f"expires_at: {expires_at_aware}, agora: {agora}")

                    # Chamada com parâmetros configurados
                    offer_status = steam_client.get_trade_offer(oferta.tradeofferid, merge=False, use_webtoken=True)
                    print(f"Resposta da API para oferta {oferta.tradeofferid}: {offer_status}")

                    if ('response' not in offer_status or 'offer' not in offer_status['response'] or not offer_status['response']['offer']):
                        print(f"Oferta {oferta.tradeofferid}: resposta vazia ou inválida da API.")
                        if agora > expires_at_aware:
                            print(f"Atualizando status da oferta {oferta.tradeofferid} para 'cancelado' por expiração (sem dados da API).")
                            try:
                                steam_client.cancel_trade_offer(oferta.tradeofferid)
                                print(f"Método cancel_trade_offer chamado para oferta {oferta.tradeofferid}.")
                            except Exception as cancel_e:
                                print(f"Erro ao chamar cancel_trade_offer: {cancel_e}")
                            oferta.status = 'cancelado'
                            oferta.cancelado_por = 'site'
                            oferta.updated_at = datetime.now(timezone.utc)
                            db.session.commit()
                            print(f"Oferta {oferta.tradeofferid} atualizada para cancelado.")
                        else:
                            print(f"Oferta {oferta.tradeofferid} ainda não está expirada.")
                        continue

                    novo_status = offer_status['response']['offer'].get('trade_offer_state')
                    if novo_status is None:
                        print(f"Não foi possível obter 'trade_offer_state' para a oferta {oferta.tradeofferid}.")
                        novo_status_str = 'desconhecido'
                    else:
                        status_map = {
                            1: 'pendente',
                            2: 'aceito',
                            3: 'cancelado',
                            4: 'contra-ofertada',
                            5: 'expirada',
                            6: 'cancelado',
                            7: 'recusada',
                            8: 'itens inválidos',
                            9: 'criada, precisa de confirmação',
                            10: 'cancelado',
                            11: 'em custódia'
                        }
                        novo_status_str = status_map.get(novo_status, 'desconhecido')

                    oferta.status = novo_status_str
                    if novo_status_str == 'cancelado':
                        if novo_status == 7:
                            oferta.status = 'recusada'
                            oferta.cancelado_por = 'usuario'
                        else:
                            oferta.cancelado_por = 'usuario'
                    else:
                        oferta.cancelado_por = None
                    oferta.updated_at = datetime.now(timezone.utc)
                    db.session.commit()
                    print(f"Oferta {oferta.tradeofferid} atualizada para {oferta.status} via API.")

                    if oferta.status == 'pendente' and agora > expires_at_aware:
                        print(f"Cancelando oferta {oferta.tradeofferid} por expiração...")
                        try:
                            steam_client.cancel_trade_offer(oferta.tradeofferid)
                            print(f"Método cancel_trade_offer chamado para oferta {oferta.tradeofferid}.")
                        except Exception as cancel_e:
                            print(f"Erro ao chamar cancel_trade_offer: {cancel_e}")
                        oferta.status = 'cancelado'
                        oferta.cancelado_por = 'site'
                        oferta.updated_at = datetime.now(timezone.utc)
                        db.session.commit()
                        print(f"Oferta {oferta.tradeofferid} cancelada automaticamente pelo site.")

                except Exception as e:
                    print(f"Erro ao verificar oferta {oferta.tradeofferid}: {e}")
                    db.session.rollback()

        except Exception as e:
            print(f"Erro no loop de verificação: {e}")

        time.sleep(60)

if __name__ == "__main__":
    from app import create_app
    app = create_app()
    with app.app_context():
        verificar_status_ofertas()