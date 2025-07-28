import os
import json
import time
import requests
from dotenv import load_dotenv
from models import TradeOffer

load_dotenv()

class SteamWebAPI:
    def __init__(self):
        self.api_key = os.getenv("STEAM_API_KEY")
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def send_trade_offer(self, partner_id, asset_ids, trade_token, message="Trade offer from TitoSkins"):
        """
        Envia uma trade offer usando a Steam Web API diretamente
        """
        try:
            # Carregar credenciais Steam Guard
            with open("config/steam/steam_guard.json", "r") as f:
                steam_guard = json.load(f)
            
            steam_id = steam_guard["steam_id"]
            
            print(f"🔄 Enviando trade offer via Steam Web API...")
            print(f"📤 Partner: {partner_id}")
            print(f"📦 Assets: {asset_ids}")
            print(f"🔑 Token: {trade_token}")
            
            # Preparar os itens para trade
            items_to_give = []
            for asset_id in asset_ids:
                items_to_give.append({
                    "appid": 730,  # CS2/CS:GO
                    "contextid": "2",
                    "assetid": str(asset_id)
                })
            
            # Parâmetros da trade offer
            trade_offer_params = {
                "newversion": True,
                "version": 4,
                "me": {
                    "assets": [],  # ✅ EU não dou nada (sou comprador)
                    "currency": [],
                    "ready": False
                },
                "them": {
                    "assets": items_to_give,  # ✅ ELES dão os itens (são vendedores)
                    "currency": [],
                    "ready": False
                }
            }
            
            # DESCOBERTA CRÍTICA: Steam Web API NÃO possui endpoint SendTradeOffer
            # O endpoint IEconService/SendTradeOffer/v1/ retorna HTTP 404 (Not Found)
            # 
            # FATO: A Steam Web API pública só permite CONSULTAR trade offers existentes:
            # - IEconService/GetTradeOffers - listar offers
            # - IEconService/GetTradeOffer - consultar offer específica
            # - IEconService/GetTradeHistory - histórico de trades
            #
            # Para ENVIAR trade offers é necessário usar:
            # 1. Steam Client SDK (oficial, C++)  
            # 2. aiosteampy/steampy (emulam cliente Steam)
            #
            # ERRO IDENTIFICADO: Nosso fallback estava usando endpoint inexistente
            
            print(f"❌ ERRO CRÍTICO: Steam Web API não suporta SendTradeOffer")
            print(f"📋 Endpoint testado: https://api.steampowered.com/IEconService/SendTradeOffer/v1/")
            print(f"🔍 Resultado: HTTP 404 Not Found")
            print(f"✅ Solução: Corrigir aiosteampy login para funcionar corretamente")
            
            return {
                "success": False,
                "error": "endpoint_not_exists",
                "message": "Steam Web API não possui endpoint SendTradeOffer (HTTP 404)",
                "details": {
                    "tested_endpoint": "IEconService/SendTradeOffer/v1/",
                    "available_endpoints": [
                        "IEconService/GetTradeOffers - consultar offers",
                        "IEconService/GetTradeOffer - consultar offer específica", 
                        "IEconService/GetTradeHistory - histórico de trades"
                    ],
                    "solution": "Usar aiosteampy para envio de trade offers",
                    "ready": False
                }
            }
                
        except Exception as e:
            print(f"❌ Erro crítico: {type(e).__name__}: {str(e)}")
            return {
                "success": False,
                "error": "critical_error",
                "message": f"Erro crítico: {str(e)}"
            }

def enviar_oferta_steam_web_api(partner_id, asset_ids, trade_token):
    """
    Função wrapper para compatibilidade com o código existente
    """
    api = SteamWebAPI()
    return api.send_trade_offer(partner_id, asset_ids, trade_token)
