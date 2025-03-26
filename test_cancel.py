from app import create_app
from datetime import datetime, timezone
import os
from steampy.client import SteamClient


STEAM_API_KEY = os.getenv("STEAM_API_KEY")
STEAM_USERNAME = os.getenv("STEAM_USERNAME")
STEAM_PASSWORD = os.getenv("STEAM_PASSWORD")
STEAM_GUARD_PATH = "./steam_guard.json"  

def testar_cancelamento(offer_id):
    # Cria a instância do SteamClient
    steam_client = SteamClient(STEAM_API_KEY)
    try:
        steam_client.login(STEAM_USERNAME, STEAM_PASSWORD, STEAM_GUARD_PATH)
        print("Login realizado com sucesso!")
    except Exception as e:
        print("Erro no login:", e)
        return

    print(f"Tentando cancelar a oferta {offer_id}...")
    try:
        result = steam_client.cancel_trade_offer(offer_id)
        print(f"Resultado do cancelamento: {result}")
    except Exception as e:
        print(f"Erro ao cancelar a oferta {offer_id}: {e}")

if __name__ == "__main__":
    # Para garantir que, se o método cancel_trade_offer utilizar algum recurso do Flask,
    # podemos criar um app context (se necessário):
    app = create_app()
    with app.app_context():
        testar_cancelamento("7763490176")  # Substitua pelo tradeofferid desejado para teste
