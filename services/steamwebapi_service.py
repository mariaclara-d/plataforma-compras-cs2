import aiohttp
import asyncio
import json
import logging
import time
import hmac
import hashlib
import struct
import base64
import os
from pathlib import Path
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class RateLimitTracker:
    """Controle de rate limiting para SteamWebAPI"""
    def __init__(self):
        self.requests = []
        self.max_requests = 2  # Free plan: 2 requests per 60 seconds
        self.time_window = 60  # 60 seconds
    
    def can_make_request(self):
        """Verifica se pode fazer nova requisição"""
        now = datetime.now()
        # Remove requests antigos (fora da janela de tempo)
        self.requests = [req_time for req_time in self.requests 
                        if now - req_time < timedelta(seconds=self.time_window)]
        
        return len(self.requests) < self.max_requests
    
    def record_request(self):
        """Registra nova requisição"""
        self.requests.append(datetime.now())
    
    def time_until_next_request(self):
        """Retorna tempo em segundos até próxima requisição permitida"""
        if self.can_make_request():
            return 0
        
        oldest_request = min(self.requests)
        time_since_oldest = datetime.now() - oldest_request
        return self.time_window - time_since_oldest.total_seconds()

class SteamWebAPIService:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://www.steamwebapi.com/steam/api"
        self.session = None
        self.rate_limiter = RateLimitTracker()
        
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
        """Obter steamLoginSecure cookie via API com rate limiting e retry"""

        logger.info("[STEAMWEBAPI] === OBTENDO steamLoginSecure ===")
        
        max_retries = 3
        base_delay = 5  # 5 segundos entre tentativas
        
        for attempt in range(max_retries):
            try:
                # Verificar rate limiting
                if not self.rate_limiter.can_make_request():
                    wait_time = self.rate_limiter.time_until_next_request()
                    logger.warning(f"[RATE_LIMIT] Aguardando {wait_time:.1f}s antes da próxima requisição")
                    await asyncio.sleep(wait_time)

                # Registrar requisição para rate limiting
                self.rate_limiter.record_request()
                
                # Payload correto
                payload = {
                    "username": username,
                    "password": password,
                    "code": shared_secret  # ← Envie o shared_secret, não o código 2FA
                }

                endpoint = f"{self.base_url}/steamloginsecure?key={self.api_key}"

                logger.info(f"[STEAMWEBAPI] Tentativa {attempt + 1}/{max_retries}")
                logger.info(f"[STEAMWEBAPI] DEBUG - Endpoint: {endpoint}")
                logger.info(f"[STEAMWEBAPI] DEBUG - Username: {username}")
                logger.info(f"[STEAMWEBAPI] DEBUG - Password: {'*' * len(password)}")
                logger.info(f"[STEAMWEBAPI] DEBUG - Shared Secret (primeiros 10 chars): {shared_secret[:10]}...")
                logger.info(f"[STEAMWEBAPI] Fazendo login para: {username}")

                # Timeout progressivo: 30s, 45s, 60s
                timeout_seconds = 30 + (attempt * 15)
                timeout = aiohttp.ClientTimeout(total=timeout_seconds)
                
                async with self.session.post(endpoint, json=payload, timeout=timeout) as response:
                    response_text = await response.text()
                    logger.info(f"[STEAMWEBAPI] Status: {response.status}")
                    logger.info(f"[STEAMWEBAPI] Response Body: {response_text}")

                    if response.status == 200:
                        try:
                            result = json.loads(response_text)
                            steam_cookie = result.get('cookies', {}).get('steamloginsecure')
                            
                            if steam_cookie:
                                logger.info("[STEAMWEBAPI]  steamLoginSecure obtido com sucesso!")
                                logger.info(f"[STEAMWEBAPI] Cookie: {steam_cookie[:50]}...")
                                return steam_cookie
                            else:
                                logger.error(f"[STEAMWEBAPI]  Erro: Campo steamloginsecure não encontrado no response")
                                logger.error(f"[STEAMWEBAPI]  Response completo: {result}")
                                raise Exception(f"Campo steamloginsecure não encontrado: {result}")

                        except json.JSONDecodeError as e:
                            logger.error(f"[STEAMWEBAPI]  Resposta não é JSON: {e}")
                            logger.error(f"[STEAMWEBAPI]  Response raw: {response_text}")
                            raise Exception(f"Resposta inválida da API: {response_text}")
                    else:
                        logger.error(f"[STEAMWEBAPI]  HTTP {response.status}: {response_text}")
                        raise Exception(f"Erro HTTP {response.status}: {response_text}")

            except asyncio.TimeoutError:
                logger.warning(f"[STEAMWEBAPI]  Timeout na tentativa {attempt + 1}/{max_retries}")
                if attempt < max_retries - 1:
                    delay = base_delay * (attempt + 1)
                    logger.info(f"[STEAMWEBAPI] Aguardando {delay}s antes de tentar novamente...")
                    await asyncio.sleep(delay)
                    continue
                else:
                    logger.error("[STEAMWEBAPI]  Timeout final na requisição steamLoginSecure")
                    raise Exception("Timeout ao conectar com SteamWebAPI após 3 tentativas")
                    
            except aiohttp.ClientError as e:
                logger.warning(f"[STEAMWEBAPI]  Erro de conexão na tentativa {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    delay = base_delay * (attempt + 1)
                    logger.info(f"[STEAMWEBAPI] Aguardando {delay}s antes de tentar novamente...")
                    await asyncio.sleep(delay)
                    continue
                else:
                    logger.error(f"[STEAMWEBAPI]  Erro de conexão final: {e}")
                    raise Exception(f"Erro de conexão com SteamWebAPI: {e}")
                    
            except Exception as e:
                logger.error(f"[STEAMWEBAPI]  Erro ao obter steamLoginSecure: {e}")
                raise
    
    async def create_trade_offer(self, steam_cookie, trade_data):
        """Criar trade offer - apenas RECEBENDO itens do usuário"""
        
        logger.info("[STEAMWEBAPI] === CRIANDO TRADE OFFER ===")
        
        try:
            # Endpoint oficial com API key
            endpoint = f"{self.base_url}/trade/create?key={self.api_key}"
            
            # Converter lista de asset IDs para string separada por vírgulas
            if isinstance(trade_data['items_to_receive'], list):
                if trade_data['items_to_receive'] and isinstance(trade_data['items_to_receive'][0], dict):
                    # Lista de objetos com assetid
                    partner_asset_ids = ",".join([str(item['assetid']) for item in trade_data['items_to_receive']])
                else:
                    # Lista simples de assetids
                    partner_asset_ids = ",".join([str(assetid) for assetid in trade_data['items_to_receive']])
            else:
                partner_asset_ids = str(trade_data['items_to_receive'])
            
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
                            
                            logger.info(f"[STEAMWEBAPI]  TRADE OFFER CRIADA! ID: {trade_offer_id}")
                            
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
                            logger.error(f"[STEAMWEBAPI]  Erro da API: {error_msg}")
                            
                            return {
                                'success': False,
                                'error': error_msg,
                                'message': f'Erro ao criar trade offer: {error_msg}',
                                'method': 'SteamWebAPI'
                            }
                            
                    except json.JSONDecodeError as e:
                        logger.error(f"[STEAMWEBAPI]  Resposta não é JSON: {e}")
                        return {
                            'success': False,
                            'error': 'Resposta inválida',
                            'message': f'API retornou resposta inválida: {response_text}',
                            'method': 'SteamWebAPI'
                        }
                
                # Tratar códigos de erro específicos da documentação
                elif response.status == 401:
                    logger.error("[STEAMWEBAPI]  401: steamloginsecure inválido ou expirado")
                    return {
                        'success': False,
                        'error': 'Unauthorized',
                        'message': 'steamloginsecure inválido ou expirado. É necessário fazer novo login.',
                        'method': 'SteamWebAPI'
                    }
                elif response.status == 402:
                    logger.error("[STEAMWEBAPI]  402: Rate limit excedido")
                    return {
                        'success': False,
                        'error': 'Rate limit exceeded',
                        'message': 'Limite de requisições diárias/mensais excedido.',
                        'method': 'SteamWebAPI'
                    }
                elif response.status == 406:
                    logger.error("[STEAMWEBAPI]  406: Asset ID inválido ou muitas trade offers pendentes")
                    return {
                        'success': False,
                        'error': 'Invalid asset ID',
                        'message': 'Asset ID inválido ou muitas trade offers pendentes.',
                        'method': 'SteamWebAPI'
                    }
                elif response.status == 409:
                    logger.error("[STEAMWEBAPI]  409: Muitos cancelamentos recentes")
                    return {
                        'success': False,
                        'error': 'Too many cancellations',
                        'message': 'Falha na criação - muitos cancelamentos recentes.',
                        'method': 'SteamWebAPI'
                    }
                elif response.status == 429:
                    logger.error("[STEAMWEBAPI]  429: Rate limit excedido")
                    return {
                        'success': False,
                        'error': 'Rate limit exceeded',
                        'message': 'Muitas requisições. Aguarde antes de tentar novamente.',
                        'method': 'SteamWebAPI'
                    }
                else:
                    logger.error(f"[STEAMWEBAPI]  HTTP {response.status}: {response_text}")
                    return {
                        'success': False,
                        'error': f'HTTP {response.status}',
                        'message': f'Erro HTTP {response.status}: {response_text}',
                        'method': 'SteamWebAPI'
                    }
                    
        except Exception as e:
            logger.error(f"[STEAMWEBAPI]  Erro ao criar trade offer: {e}")
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
        # Carregar credenciais Steam do .env
        username = os.getenv('STEAM_USERNAME')
        password = os.getenv('STEAM_PASSWORD') 
        shared_secret = os.getenv('STEAM_SHARED_SECRET')
        
        if not all([username, password, shared_secret]):
            # Fallback: tentar carregar do arquivo se .env não tiver
            steam_config_file = Path("config/steam/steam_guard.json")
            if steam_config_file.exists():
                with open(steam_config_file, 'r', encoding='utf-8') as f:
                    steam_config = json.load(f)
                username = username or steam_config.get('username')
                password = password or steam_config.get('password')
                shared_secret = shared_secret or steam_config.get('code')
            
            if not all([username, password, shared_secret]):
                raise ValueError("Credenciais Steam não configuradas no .env ou steam_guard.json")
        
        # Carregar API key do .env
        api_key = os.getenv('STEAMWEBAPI_KEY')
        
        if not api_key:
            # Fallback: tentar carregar do arquivo de configuração
            api_config_file = Path("config/steamwebapi/config.json")
            if api_config_file.exists():
                with open(api_config_file, 'r', encoding='utf-8') as f:
                    api_config = json.load(f)
                api_key = api_config.get('api_key')
        
        if not api_key or api_key == "SUA_API_KEY_STEAMWEBAPI_AQUI":
            raise ValueError("STEAMWEBAPI_KEY não configurada no .env")
        
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
        
        logger.info(f"[MAIN]  SteamWebAPI result: {result}")
        return result
        
    except Exception as e:
        logger.error(f"[MAIN] Erro SteamWebAPI: {e}")
        return {
            'success': False,
            'error': str(e),
            'message': f'Erro ao processar via SteamWebAPI: {e}',
            'method': 'SteamWebAPI'
        }