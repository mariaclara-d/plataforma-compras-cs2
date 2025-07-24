# services/inventory_service.py
import os
import requests
import json
import logging
from typing import List, Dict, Optional, Any
from flask import current_app
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class InventoryItem:
    """Representa um item do inventário com todas as informações necessárias"""
    
    def __init__(self, data: Dict[str, Any]):
        # Dados básicos do item
        self.assetid = data.get('assetid', '')
        self.classid = data.get('classid', '')
        self.instanceid = data.get('instanceid', '')
        self.name = data.get('market_hash_name', data.get('marketname', data.get('name', '')))
        self.type = data.get('type', '')
        self.icon_url = data.get('icon_url', '')
        
        # URLs de imagem
        self.image_url = self._build_image_url(data.get('image', data.get('icon_url', '')))
        
        # Preços (da API alternativa)
        self.price_median = data.get('price_median', data.get('pricemedian', 'N/A'))
        self.price_safe = data.get('price_safe', data.get('pricesafe', 'N/A'))
        self.price_max = data.get('price_max', data.get('pricemax', 'N/A'))
        self.price_min = data.get('price_min', data.get('pricemin', 'N/A'))
        self.price_avg = data.get('price_avg', data.get('priceavg', 'N/A'))
        
        # Link de inspeção
        self.inspect_link = data.get('inspect_link', data.get('inspectlink', '#'))
        
        # Outras propriedades
        self.tradable = data.get('tradable', False)
        self.rarity = data.get('rarity', 'N/A')
        self.quality = data.get('quality', 'N/A')
        
        # Dados originais para debug
        self.raw_data = data
    
    def _build_image_url(self, image_url: str) -> str:
        """Constrói a URL completa da imagem"""
        if not image_url:
            return ''
        
        # Se já tem o domínio, retorna como está
        if image_url.startswith('http'):
            return image_url
        
        # Se é apenas o hash, constrói a URL completa
        base_url = "https://steamcommunity-a.akamaihd.net/economy/image/"
        return f"{base_url}{image_url}/330x192"
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte o item para dicionário para uso em templates"""
        return {
            'assetid': self.assetid,
            'classid': self.classid,
            'instanceid': self.instanceid,
            'name': self.name,
            'type': self.type,
            'image_url': self.image_url,
            'price_median': self.price_median,
            'price_safe': self.price_safe,
            'price_max': self.price_max,
            'price_min': self.price_min,
            'price_avg': self.price_avg,
            'inspect_link': self.inspect_link,
            'tradable': self.tradable,
            'rarity': self.rarity,
            'quality': self.quality
        }

class InventoryService:
    """Serviço centralizado para gerenciamento de inventário Steam"""
    
    def __init__(self):
        self.steam_api_key = os.getenv("STEAM_API_KEY_NAO_OFICIAL")
        self.alternative_api_url = "https://www.steamwebapi.com/steam/api/inventory"
        self.steam_inventory_url = "https://steamcommunity.com/inventory"
        self.logger = logging.getLogger(__name__)
    
    def validate_tradelink(self, tradelink: str, user_steam_id: str) -> bool:
        """Valida se o tradelink corresponde ao usuário logado"""
        try:
            tradelink_steam_id = tradelink.split("partner=")[1].split("&")[0]
            partner_id = int(tradelink_steam_id)
            calculated_steam_id = str(partner_id + 76561197960265728)
        except (IndexError, ValueError):
            self.logger.warning("Tradelink está no formato incorreto.")
            return False

        user_steam_id = user_steam_id.replace("https://steamcommunity.com/openid/id/", "")

        if calculated_steam_id != user_steam_id:
            self.logger.warning(f"Tradelink ID ({calculated_steam_id}) não corresponde ao user_steam_id ({user_steam_id}).")
            return False

        self.logger.info("Tradelink validado com sucesso!")
        return True
    
    def fetch_inventory_alternative_api(self, steam_id: str) -> List[InventoryItem]:
        """
        Busca inventário usando API alternativa (steamwebapi.com)
        Esta API já retorna preços e informações processadas
        """
        self.logger.info(f"Buscando inventário via API alternativa para Steam ID: {steam_id}")
        
        # Limpar steam_id se necessário
        if steam_id.startswith("https://steamcommunity.com/openid/id/"):
            steam_id = steam_id.replace("https://steamcommunity.com/openid/id/", "")
        
        try:
            # URL da API alternativa
            url = f"{self.alternative_api_url}?key={self.steam_api_key}&steam_id={steam_id}"
            
            self.logger.debug(f"Fazendo requisição para: {url}")
            
            response = requests.get(url, timeout=30)
            
            self.logger.debug(f"Status da resposta: {response.status_code}")
            
            if response.status_code != 200:
                self.logger.error(f"Erro na API alternativa: Status {response.status_code}")
                self.logger.error(f"Resposta: {response.text}")
                return []
            
            data = response.json()
            self.logger.debug(f"Dados recebidos da API alternativa: {len(data) if isinstance(data, list) else 'não é lista'}")
            
            if not isinstance(data, list):
                self.logger.warning("Resposta da API alternativa não é uma lista")
                return []
            
            if not data:
                self.logger.warning("Nenhum item encontrado na resposta da API alternativa")
                return []
            
            # Converter para objetos InventoryItem
            inventory_items = []
            for item_data in data:
                try:
                    item = InventoryItem(item_data)
                    inventory_items.append(item)
                    self.logger.debug(f"Item processado: {item.name} (assetid: {item.assetid})")
                except Exception as e:
                    self.logger.error(f"Erro ao processar item: {e}")
                    self.logger.error(f"Dados do item: {item_data}")
            
            # Log único e centralizado dos assetids
            assetids = [item.assetid for item in inventory_items]
            self.logger.info(f"[INVENTORY_SERVICE] {len(inventory_items)} itens carregados para usuário {steam_id}")
            self.logger.info(f"[INVENTORY_SERVICE] AssetIDs disponíveis: {assetids}")
            
            return inventory_items
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Erro de rede ao buscar inventário via API alternativa: {e}")
            return []
        except json.JSONDecodeError as e:
            self.logger.error(f"Erro ao decodificar JSON da API alternativa: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Erro inesperado na API alternativa: {e}")
            return []
    
    def fetch_inventory_steam_api(self, steam_id: str) -> List[Dict[str, Any]]:
        """
        Busca inventário usando API oficial do Steam
        Retorna dados brutos para comparação de assetids
        """
        self.logger.info(f"Buscando inventário via API Steam oficial para Steam ID: {steam_id}")
        
        # Limpar steam_id se necessário
        if steam_id.startswith("https://steamcommunity.com/openid/id/"):
            steam_id = steam_id.replace("https://steamcommunity.com/openid/id/", "")
        
        try:
            # URL da API oficial do Steam
            url = f"{self.steam_inventory_url}/{steam_id}/730/2"
            
            self.logger.debug(f"Fazendo requisição para Steam API: {url}")
            
            # Headers para a requisição
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            
            self.logger.debug(f"Status da resposta Steam API: {response.status_code}")
            
            if response.status_code != 200:
                self.logger.error(f"Erro na Steam API: Status {response.status_code}")
                self.logger.error(f"Resposta: {response.text}")
                return []
            
            data = response.json()
            self.logger.debug(f"Estrutura da resposta Steam API: {list(data.keys())}")
            
            # A Steam API retorna assets e descriptions separadamente
            assets = data.get('assets', [])
            descriptions = data.get('descriptions', [])
            
            self.logger.info(f"Steam API - Assets: {len(assets)}, Descriptions: {len(descriptions)}")
            
            # Log dos primeiros assetids para debug
            if assets:
                first_assets = assets[:5]  # Primeiros 5 para não logar demais
                for asset in first_assets:
                    self.logger.debug(f"Steam API Asset: assetid={asset.get('assetid')}, classid={asset.get('classid')}")
            
            return assets
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Erro de rede ao buscar inventário via Steam API: {e}")
            return []
        except json.JSONDecodeError as e:
            self.logger.error(f"Erro ao decodificar JSON da Steam API: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Erro inesperado na Steam API: {e}")
            return []
    
    def fetch_inventory_steam_api_as_items(self, steam_id: str) -> List[InventoryItem]:
        """
        Busca inventário usando API oficial do Steam e converte para InventoryItem
        Usado como fallback quando a API alternativa falha
        """
        self.logger.info(f"Usando Steam API oficial como fonte principal para Steam ID: {steam_id}")
        
        # Limpar steam_id se necessário
        if steam_id.startswith("https://steamcommunity.com/openid/id/"):
            steam_id = steam_id.replace("https://steamcommunity.com/openid/id/", "")
        
        try:
            # URL da API oficial do Steam
            url = f"{self.steam_inventory_url}/{steam_id}/730/2"
            
            self.logger.debug(f"Fazendo requisição para Steam API: {url}")
            
            # Headers para a requisição
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            
            self.logger.debug(f"Status da resposta Steam API: {response.status_code}")
            
            if response.status_code != 200:
                self.logger.error(f"Erro na Steam API: Status {response.status_code}")
                self.logger.error(f"Resposta: {response.text}")
                return []
            
            data = response.json()
            self.logger.debug(f"Estrutura da resposta Steam API: {list(data.keys())}")
            
            # A Steam API retorna assets e descriptions separadamente
            assets = data.get('assets', [])
            descriptions = data.get('descriptions', [])
            
            self.logger.info(f"Steam API - Assets: {len(assets)}, Descriptions: {len(descriptions)}")
            
            if not assets:
                self.logger.warning("Nenhum asset encontrado na Steam API")
                return []
            
            # Criar um dicionário de descriptions por classid+instanceid
            desc_map = {}
            for desc in descriptions:
                key = f"{desc.get('classid')}_{desc.get('instanceid', '0')}"
                desc_map[key] = desc
            
            # Converter assets para InventoryItem
            inventory_items = []
            for asset in assets:
                try:
                    # Buscar description correspondente
                    key = f"{asset.get('classid')}_{asset.get('instanceid', '0')}"
                    desc = desc_map.get(key, {})
                    
                    # Combinar dados do asset e description
                    item_data = {
                        'assetid': asset.get('assetid'),
                        'classid': asset.get('classid'),
                        'instanceid': asset.get('instanceid'),
                        'market_hash_name': desc.get('market_hash_name', desc.get('name', 'Unknown')),
                        'name': desc.get('name', 'Unknown'),
                        'type': desc.get('type', ''),
                        'icon_url': desc.get('icon_url', ''),
                        'tradable': desc.get('tradable', 1) == 1,
                        'marketable': desc.get('marketable', 1) == 1,
                        # Preços não disponíveis na Steam API oficial
                        'price_median': 'N/A',
                        'price_safe': 'N/A', 
                        'price_max': 'N/A',
                        'price_min': 'N/A',
                        'price_avg': 'N/A',
                        'inspect_link': '#'  # Não disponível na Steam API oficial
                    }
                    
                    item = InventoryItem(item_data)
                    inventory_items.append(item)
                    self.logger.debug(f"Item Steam API processado: {item.name} (assetid: {item.assetid})")
                    
                except Exception as e:
                    self.logger.error(f"Erro ao processar asset da Steam API: {e}")
                    self.logger.error(f"Asset data: {asset}")
                    self.logger.error(f"Description data: {desc}")
            
            # Log único e centralizado dos assetids
            assetids = [item.assetid for item in inventory_items]
            self.logger.info(f"[STEAM_API_FALLBACK] {len(inventory_items)} itens carregados para usuário {steam_id}")
            self.logger.info(f"[STEAM_API_FALLBACK] AssetIDs disponíveis: {assetids}")
            
            return inventory_items
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Erro de rede ao buscar inventário via Steam API fallback: {e}")
            return []
        except json.JSONDecodeError as e:
            self.logger.error(f"Erro ao decodificar JSON da Steam API fallback: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Erro inesperado na Steam API fallback: {e}")
            return []
    
    def get_user_inventory(self, steam_id: str) -> List[InventoryItem]:
        """
        Método principal para obter inventário do usuário
        Usa APENAS a API alternativa para exibir inventário (com preços)
        A Steam API oficial é usada APENAS para validação de assetids
        """
        self.logger.info(f"Iniciando busca de inventário para Steam ID: {steam_id}")
        
        # 1. Buscar via API alternativa (ÚNICA fonte para exibir inventário)
        inventory_items = self.fetch_inventory_alternative_api(steam_id)
        
        # 2. Se a API alternativa falhou, usar Steam API como fallback temporário para TESTE
        if not inventory_items:
            self.logger.warning("API alternativa falhou - usando Steam API oficial como fallback para teste")
            # return []  # Comentado temporariamente para permitir fallback
        
        # 3. Buscar via Steam API oficial SEMPRE (para validação ou fallback)
        steam_assets = self.fetch_inventory_steam_api(steam_id)
        
        # 3.1. Se API alternativa falhou, criar itens básicos da Steam API para teste
        if not inventory_items and steam_assets:
            self.logger.warning("Criando itens básicos da Steam API para teste")
            inventory_items = []
            
            # Buscar descriptions também (necessário para nomes e ícones)
            try:
                url = f"{self.steam_inventory_url}/{steam_id}/730/2"
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'application/json'
                }
                response = requests.get(url, headers=headers, timeout=30)
                if response.status_code == 200:
                    data = response.json()
                    descriptions = data.get('descriptions', [])
                    
                    # Criar um mapa de descriptions por classid+instanceid
                    desc_map = {}
                    for desc in descriptions:
                        key = f"{desc.get('classid')}_{desc.get('instanceid', 0)}"
                        desc_map[key] = desc
                    
                    # Criar itens básicos fazendo join entre assets e descriptions
                    for asset in steam_assets[:10]:  # Limitar a 10 itens para teste
                        if asset.get('assetid'):
                            # Buscar description correspondente
                            key = f"{asset.get('classid')}_{asset.get('instanceid', 0)}"
                            desc = desc_map.get(key, {})
                            
                            # Criar dados para InventoryItem
                            item_data = {
                                'assetid': asset['assetid'],
                                'classid': asset.get('classid'),
                                'instanceid': asset.get('instanceid'),
                                'market_hash_name': desc.get('market_hash_name', f'Item {asset["assetid"]}'),
                                'icon_url': desc.get('icon_url', ''),
                                'price_median': 1.0,  # Preço padrão para teste
                                'tradable': desc.get('tradable', 1) == 1,
                                'marketable': desc.get('marketable', 1) == 1
                            }
                            
                            basic_item = InventoryItem(item_data)
                            inventory_items.append(basic_item)
                            
            except Exception as e:
                self.logger.error(f"Erro ao buscar descriptions da Steam API: {e}")
                # Fallback: criar itens básicos apenas com assetid
                for asset in steam_assets[:10]:
                    if asset.get('assetid'):
                        item_data = {
                            'assetid': asset['assetid'],
                            'classid': asset.get('classid'),
                            'instanceid': asset.get('instanceid'),
                            'market_hash_name': f'Item {asset["assetid"]}',
                            'icon_url': '',
                            'price_median': 1.0,
                            'tradable': True,
                            'marketable': True
                        }
                        basic_item = InventoryItem(item_data)
                        inventory_items.append(basic_item)
                        
            self.logger.info(f"Criados {len(inventory_items)} itens básicos para teste")
        
        # 4. Criar conjunto de assetids válidos da Steam API
        valid_assetids = set()
        if steam_assets:
            valid_assetids = {asset.get('assetid') for asset in steam_assets if asset.get('assetid')}
            self.logger.info(f"AssetIDs válidos encontrados na Steam API: {len(valid_assetids)}")
            
            # Log de alguns assetids para comparação
            if valid_assetids:
                sample_ids = list(valid_assetids)[:5]
                self.logger.debug(f"Exemplos de assetids válidos: {sample_ids}")
        
        # 5. Filtrar itens da API alternativa usando assetids válidos da Steam API
        if valid_assetids:
            filtered_items = []
            invalid_items = []
            
            for item in inventory_items:
                if item.assetid in valid_assetids:
                    filtered_items.append(item)
                    self.logger.debug(f"Item válido: {item.name} (assetid: {item.assetid})")
                else:
                    invalid_items.append(item)
                    self.logger.warning(f"AssetID inválido: {item.assetid} para item {item.name}")
            
            self.logger.info(f"Itens válidos: {len(filtered_items)}, Itens inválidos: {len(invalid_items)}")
            
            # Se temos muitos itens inválidos, pode ser um problema de sincronia
            if len(invalid_items) > len(filtered_items):
                self.logger.warning("Muitos assetids inválidos encontrados - possível problema de sincronia entre APIs")
            
            return filtered_items
        else:
            self.logger.warning("Nenhum assetid válido encontrado na Steam API - retornando todos os itens da API alternativa")
            return inventory_items
    
    def get_inventory(self, user_steam_id: str) -> List[Dict[str, Any]]:
        """
        Método de compatibilidade - retorna inventário como lista de dicionários
        Mantém compatibilidade com código existente
        """
        inventory_items = self.get_user_inventory(user_steam_id)
        return [item.to_dict() for item in inventory_items]
    
    def fetch_inventory(self, tradelink: str, user_steam_id: str) -> Dict[str, Any]:
        """Função principal para buscar inventário validado"""
        if not self.validate_tradelink(tradelink, user_steam_id):
            return {"error": "Tradelink não corresponde ao usuário logado."}, 400
        
        inventory = self.get_inventory(user_steam_id)
        
        return {
            "steam_id": user_steam_id,
            "tradelink": tradelink,
            "inventory": inventory
        }
    
    def validate_selected_items(self, selected_assetids: List[str], steam_id: str) -> Dict[str, Any]:
        """
        Valida se os assetids selecionados são válidos no inventário atual
        Usa Steam API oficial como fallback quando API alternativa falha
        """
        self.logger.info(f"Validando {len(selected_assetids)} itens selecionados")
        
        # Tentar buscar inventário atual via API alternativa primeiro
        current_inventory = self.get_user_inventory(steam_id)
        
        # Se API alternativa falhou, usar Steam API oficial apenas para validação
        if not current_inventory:
            self.logger.warning("API alternativa falhou - usando Steam API oficial apenas para validação de assetids")
            steam_assets = self.fetch_inventory_steam_api(steam_id)
            
            if not steam_assets:
                return {
                    'valid': False,
                    'error': 'Não foi possível carregar o inventário atual via nenhuma API',
                    'valid_items': [],
                    'invalid_items': selected_assetids
                }
            
            # Criar conjunto de assetids válidos apenas da Steam API
            valid_assetids = {asset.get('assetid') for asset in steam_assets if asset.get('assetid')}
            self.logger.info(f"Steam API oficial encontrou {len(valid_assetids)} assetids válidos para validação")
            
        else:
            # Usar inventário da API alternativa
            valid_assetids = {item.assetid for item in current_inventory}
        
        # Separar itens válidos e inválidos
        valid_items = []
        invalid_items = []
        
        for assetid in selected_assetids:
            if assetid in valid_assetids:
                valid_items.append(assetid)
            else:
                invalid_items.append(assetid)
        
        self.logger.info(f"Validação concluída - Válidos: {len(valid_items)}, Inválidos: {len(invalid_items)}")
        
        if invalid_items:
            self.logger.warning(f"AssetIDs inválidos encontrados: {invalid_items}")
        
        return {
            'valid': len(invalid_items) == 0,
            'valid_items': valid_items,
            'invalid_items': invalid_items,
            'error': f'AssetIDs inválidos: {invalid_items}' if invalid_items else None
        }