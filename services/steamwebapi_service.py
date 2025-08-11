import aiohttp
import asyncio
import json
import logging
import time
import hmac
import hashlib
import struct
import base64
from pathlib import Path

logger = logging.getLogger(__name__)

class SteamWebAPIService:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://www.steamwebapi.com/steam/api"
        self.session = None
        
    async def __aenter__(self):
        """Context manager para sessão async"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                'User-Agent': 'TitoSkins/1.0',
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Fechar sessão"""
        if self.session:
            await self.session.close()
    
    def generate_2fa_code(self, shared_secret):
        """Gerar código 2FA - shared_secret está em Base64 (formato SDA)"""
        try:
            # Shared secret está em Base64 (formato original do SDA)
            key = base64.b64decode(shared_secret)
            
            # Timestamp atual dividido por 30
            timestamp = int(time.time()) // 30
            
            # Converter para bytes
            timestamp_bytes = struct.pack(">Q", timestamp)
            
            # HMAC-SHA1
            hmac_digest = hmac.new(key, timestamp_bytes, hashlib.sha1).digest()
            
            # Extrair código de 5 dígitos
            offset = hmac_digest[-1] & 0x0f
            code = struct.unpack(">I", hmac_digest[offset:offset+4])[0] & 0x7fffffff
            
            # 5 dígitos com zeros à esquerda
            return f"{code % 100000:05d}"
            
        except Exception as e:
            logger.error(f"[2FA] Erro ao gerar código: {e}")
            raise Exception(f"Erro ao gerar código 2FA: {e}")
    
    def test_2fa_code(self, shared_secret):
        """Função de teste para verificar se o código 2FA está correto"""
        try:
            code = self.generate_2fa_code(shared_secret)
            current_time = int(time.time())
            logger.info(f"[TEST] Código 2FA atual: {code}")
            logger.info(f"[TEST] Timestamp atual: {current_time}")
            logger.info(f"[TEST] Intervalo de 30s: {current_time // 30}")
            return code
        except Exception as e:
            logger.error(f"[TEST] Erro no teste 2FA: {e}")
            return None
    
    async def get_steamloginsecure(self, username, password, shared_secret):
        """Obter steamLoginSecure cookie via API"""

        logger.info("[STEAMWEBAPI] === OBTENDO steamLoginSecure ===")

        try:
            # NÃO gere o código 2FA aqui!
            # Envie o shared_secret diretamente como 'code'
            payload = {
                "username": username,
                "password": password,
                "code": shared_secret  # ← Envie o shared_secret, não o código 2FA
            }

            endpoint = f"{self.base_url}/steamloginsecure?key={self.api_key}"

            # DEBUG: Logs detalhados
            logger.info(f"[STEAMWEBAPI] DEBUG - Endpoint: {endpoint}")
            logger.info(f"[STEAMWEBAPI] DEBUG - Username: {username}")
            logger.info(f"[STEAMWEBAPI] DEBUG - Password: {'*' * len(password)}")
            logger.info(f"[STEAMWEBAPI] DEBUG - Shared Secret (primeiros 10 chars): {shared_secret[:10]}...")

            logger.info(f"[STEAMWEBAPI] Fazendo login para: {username}")

            async with self.session.post(endpoint, json=payload) as response:
                response_text = await response.text()
                logger.info(f"[STEAMWEBAPI] Status: {response.status}")

                if response.status == 200:
                    try:
                        result = json.loads(response_text)
                        steam_cookie = result.get('steamLoginSecure')
                        if steam_cookie:
                            logger.info("[STEAMWEBAPI] ✅ steamLoginSecure obtido com sucesso!")
                            logger.info(f"[STEAMWEBAPI] Cookie: {steam_cookie[:50]}...")
                            return steam_cookie
                        else:
                            error_msg = result.get('error', 'Cookie não retornado')
                            logger.error(f"[STEAMWEBAPI] ❌ Erro: {error_msg}")
                            raise Exception(f"Erro ao obter cookie: {error_msg}")

                    except json.JSONDecodeError as e:
                        logger.error(f"[STEAMWEBAPI] ❌ Resposta não é JSON: {e}")
                        raise Exception(f"Resposta inválida da API: {response_text}")
                else:
                    logger.error(f"[STEAMWEBAPI] ❌ HTTP {response.status}: {response_text}")
                    raise Exception(f"Erro HTTP {response.status}: {response_text}")

        except Exception as e:
            logger.error(f"[STEAMWEBAPI] ❌ Erro ao obter steamLoginSecure: {e}")
            raise
    
    async def create_trade_offer(self, steam_cookie, trade_data):
        """Criar trade offer - apenas RECEBENDO itens do usuário"""
        
        logger.info("[STEAMWEBAPI] === CRIANDO TRADE OFFER ===")
        
        try:
            # Endpoint oficial com API key
            endpoint = f"{self.base_url}/trade/create?key={self.api_key}"
            
            # Converter lista de asset IDs para string separada por vírgulas
            partner_asset_ids = ",".join([str(item['assetid']) for item in trade_data['items_to_receive']])
            
            # Payload conforme documentação oficial
            payload = {
                "steamloginsecure": steam_cookie,
                "partneritemassetids": partner_asset_ids,  # Itens que SOLICITAMOS do usuário
                "myitemassetids": "",                      # VAZIO - não oferecemos nada
                "tradelink": trade_data['tradelink'],
                "partnersteamid": trade_data['partner_steamid'],
                "message": trade_data.get('message', 'Venda para TitoSkins - Pagamento via PIX'),
                "game": "cs2"
            }
            
            logger.info(f"[STEAMWEBAPI] Partner SteamID: {trade_data['partner_steamid']}")
            logger.info(f"[STEAMWEBAPI] Itens SOLICITADOS: {partner_asset_ids}")
            logger.info(f"[STEAMWEBAPI] Itens OFERECIDOS: (nenhum)")
            logger.info(f"[STEAMWEBAPI] Tradelink: {trade_data['tradelink']}")
            
            async with self.session.post(endpoint, json=payload) as response:
                
                response_text = await response.text()
                logger.info(f"[STEAMWEBAPI] Status: {response.status}")
                logger.info(f"[STEAMWEBAPI] Response: {response_text}")
                
                if response.status == 200:
                    try:
                        result = json.loads(response_text)
                        
                        # Verificar se a resposta tem dados da trade offer
                        if result.get('tradeofferid') or result.get('success'):
                            trade_offer_id = result.get('tradeofferid', result.get('id', 'unknown'))
                            
                            logger.info(f"[STEAMWEBAPI] ✅ TRADE OFFER CRIADA! ID: {trade_offer_id}")
                            
                            return {
                                'success': True,
                                'tradeoffer_id': str(trade_offer_id),
                                'message': f'Trade offer criada com sucesso! ID: {trade_offer_id}. Usuário deve aceitar no Steam.',
                                'method': 'SteamWebAPI',
                                'api_response': result,
                                'instructions': 'O usuário receberá uma notificação no Steam e deve aceitar a trade offer no Steam Guard mobile.'
                            }
                        else:
                            error_msg = result.get('error', result.get('message', 'Trade offer não criada'))
                            logger.error(f"[STEAMWEBAPI] ❌ Erro da API: {error_msg}")
                            
                            return {
                                'success': False,
                                'error': error_msg,
                                'message': f'Erro ao criar trade offer: {error_msg}',
                                'method': 'SteamWebAPI'
                            }
                            
                    except json.JSONDecodeError as e:
                        logger.error(f"[STEAMWEBAPI] ❌ Resposta não é JSON: {e}")
                        return {
                            'success': False,
                            'error': 'Resposta inválida',
                            'message': f'API retornou resposta inválida: {response_text}',
                            'method': 'SteamWebAPI'
                        }
                
                # Tratar códigos de erro específicos da documentação
                elif response.status == 401:
                    logger.error("[STEAMWEBAPI] ❌ 401: steamloginsecure inválido ou expirado")
                    return {
                        'success': False,
                        'error': 'Unauthorized',
                        'message': 'steamloginsecure inválido ou expirado. É necessário fazer novo login.',
                        'method': 'SteamWebAPI'
                    }
                elif response.status == 402:
                    logger.error("[STEAMWEBAPI] ❌ 402: Rate limit excedido")
                    return {
                        'success': False,
                        'error': 'Rate limit exceeded',
                        'message': 'Limite de requisições diárias/mensais excedido.',
                        'method': 'SteamWebAPI'
                    }
                elif response.status == 406:
                    logger.error("[STEAMWEBAPI] ❌ 406: Asset ID inválido ou muitas trade offers pendentes")
                    return {
                        'success': False,
                        'error': 'Invalid asset ID',
                        'message': 'Asset ID inválido ou muitas trade offers pendentes.',
                        'method': 'SteamWebAPI'
                    }
                elif response.status == 409:
                    logger.error("[STEAMWEBAPI] ❌ 409: Muitos cancelamentos recentes")
                    return {
                        'success': False,
                        'error': 'Too many cancellations',
                        'message': 'Falha na criação - muitos cancelamentos recentes.',
                        'method': 'SteamWebAPI'
                    }
                elif response.status == 429:
                    logger.error("[STEAMWEBAPI] ❌ 429: Rate limit excedido")
                    return {
                        'success': False,
                        'error': 'Rate limit exceeded',
                        'message': 'Muitas requisições. Aguarde antes de tentar novamente.',
                        'method': 'SteamWebAPI'
                    }
                else:
                    logger.error(f"[STEAMWEBAPI] ❌ HTTP {response.status}: {response_text}")
                    return {
                        'success': False,
                        'error': f'HTTP {response.status}',
                        'message': f'Erro HTTP {response.status}: {response_text}',
                        'method': 'SteamWebAPI'
                    }
                    
        except Exception as e:
            logger.error(f"[STEAMWEBAPI] ❌ Erro ao criar trade offer: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': f'Erro inesperado: {e}',
                'method': 'SteamWebAPI'
            }


# Função wrapper principal
async def enviar_oferta_steamwebapi(partner_steamid64, items_dict, message="Venda para TitoSkins"):
    """Função principal para criar trade offer via SteamWebAPI"""
    
    logger.info("[MAIN] === USANDO STEAMWEBAPI OFICIAL ===")
    
    try:
        # Carregar configurações Steam
        steam_config_file = Path("config/steam/steam_guard.json")
        with open(steam_config_file, 'r', encoding='utf-8') as f:
            steam_config = json.load(f)
        username = steam_config['username']  # ← use 'username'
        password = steam_config['password']
        shared_secret = steam_config['code']  # ← use 'code' para o shared_secret
        
        # Carregar API key
        api_config_file = Path("config/steamwebapi/config.json")
        
        if not api_config_file.exists():
            api_config_file.parent.mkdir(parents=True, exist_ok=True)
            default_config = {
                "api_key": "SUA_API_KEY_STEAMWEBAPI_AQUI",
                "plan": "free",
                "rate_limit_per_day": 100
            }
            
            with open(api_config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=4)
            
            raise ValueError(f"Configure sua API key em: {api_config_file}")
        
        with open(api_config_file, 'r', encoding='utf-8') as f:
            api_config = json.load(f)
        
        api_key = api_config.get('api_key')
        if not api_key or api_key == "SUA_API_KEY_STEAMWEBAPI_AQUI":
            raise ValueError("API key não configurada")
        
        # Extrair dados
        tradelink = items_dict.get("tradelink")
        items = items_dict.get("itens", []) or items_dict.get("items", [])
        
        if not tradelink or not items:
            raise ValueError("Tradelink e itens são obrigatórios")
        
        # Usar o partner_steamid64 que já vem calculado do trade.py
        logger.info(f"[MAIN] Partner SteamID64 recebido: {partner_steamid64}")
        logger.info(f"[MAIN] Tradelink: {tradelink}")
        logger.info(f"[MAIN] Itens solicitados: {len(items)}")
        
        # Validação simples
        if not partner_steamid64:
            raise ValueError("Partner SteamID64 não fornecido")
        
        # Preparar dados da trade offer
        items_to_receive = []
        for item in items:
            items_to_receive.append({
                'assetid': str(item['assetid'])
            })
        
        trade_data = {
            'partner_steamid': str(partner_steamid64),
            'tradelink': tradelink,
            'items_to_receive': items_to_receive,
            'message': message
        }
        
        logger.info(f"[MAIN] Partner SteamID64: {partner_steamid64}")
        logger.info(f"[MAIN] Tradelink: {tradelink}")
        logger.info(f"[MAIN] Itens solicitados: {len(items_to_receive)}")
        
        # Usar SteamWebAPI
        async with SteamWebAPIService(api_key) as api:
            
            # 1. Obter steamLoginSecure
            logger.info("[MAIN] Obtendo steamLoginSecure...")
            steam_cookie = await api.get_steamloginsecure(username, password, shared_secret)
            
            # 2. Criar trade offer
            logger.info("[MAIN] Criando trade offer...")
            result = await api.create_trade_offer(steam_cookie, trade_data)
        
        logger.info(f"[MAIN] ✅ SteamWebAPI result: {result}")
        return result
        
    except Exception as e:
        logger.error(f"[MAIN] Erro SteamWebAPI: {e}")
        return {
            'success': False,
            'error': str(e),
            'message': f'Erro ao processar via SteamWebAPI: {e}',
            'method': 'SteamWebAPI'
        }