# services/security_service.py
import re
import html
import logging
from typing import Optional, Union, Dict, Any
from urllib.parse import urlparse
from flask import request, current_app
import time
from collections import defaultdict

logger = logging.getLogger(__name__)

class SecurityService:
    """Serviço centralizado para validações de segurança"""
    
    # Rate limiting storage (em produção, usar Redis)
    _rate_limit_storage = defaultdict(list)
    
    @staticmethod
    def sanitize_input(input_value: Union[str, None], max_length: int = 255) -> Optional[str]:
        """
        Sanitiza input removendo caracteres perigosos
        """
        if not input_value:
            return None
            
        # Converter para string e limitar tamanho
        clean_value = str(input_value)[:max_length]
        
        # Escape HTML
        clean_value = html.escape(clean_value)
        
        # Remover caracteres de controle
        clean_value = ''.join(char for char in clean_value if ord(char) >= 32 or char in '\t\n\r')
        
        # Remover SQL injection patterns básicos
        sql_patterns = [
            r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)",
            r"(--|\*\/|\/\*)",
            r"(;|\|\||&&)"
        ]
        
        for pattern in sql_patterns:
            clean_value = re.sub(pattern, '', clean_value, flags=re.IGNORECASE)
        
        return clean_value.strip()
    
    @staticmethod
    def validate_steam_id(steam_id: str) -> bool:
        """
        Valida formato de SteamID64
        """
        if not steam_id:
            return False
            
        # Limpar prefixo se necessário
        if steam_id.startswith("https://steamcommunity.com/openid/id/"):
            steam_id = steam_id.replace("https://steamcommunity.com/openid/id/", "")
        
        # SteamID64 deve ser numérico de 17 dígitos começando com 7656119
        pattern = r'^7656119[0-9]{10}$'
        return bool(re.match(pattern, steam_id))
    
    @staticmethod
    def validate_tradelink(tradelink: str) -> bool:
        """
        Valida formato de Trade Link do Steam
        """
        if not tradelink:
            return False
            
        # URL deve ser do Steam
        parsed = urlparse(tradelink)
        if parsed.netloc != 'steamcommunity.com':
            return False
            
        # Deve conter partner e token
        if 'partner=' not in tradelink or 'token=' not in tradelink:
            return False
            
        # Validar formato dos parâmetros
        partner_match = re.search(r'partner=(\d+)', tradelink)
        token_match = re.search(r'token=([a-zA-Z0-9_-]+)', tradelink)
        
        return bool(partner_match and token_match)
    
    @staticmethod
    def validate_trade_link(tradelink: str) -> bool:
        """
        Alias para validate_tradelink (compatibilidade)
        """
        return SecurityService.validate_tradelink(tradelink)
    
    @staticmethod
    def validate_assetid(assetid: str) -> bool:
        """
        Valida formato de Asset ID
        """
        if not assetid:
            return False
            
        # Asset ID deve ser numérico
        return assetid.isdigit() and len(assetid) >= 8 and len(assetid) <= 20
    
    @staticmethod
    def validate_payment_data(payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valida e sanitiza dados de pagamento
        """
        if not payment_data:
            return {"valid": False, "error": "Dados de pagamento ausentes"}
        
        method = payment_data.get('metodo_pagamento')
        if method not in ['pix', 'transfer', 'skrill']:
            return {"valid": False, "error": "Método de pagamento inválido"}
        
        result = {"valid": True, "sanitized_data": {}}
        result["sanitized_data"]["metodo_pagamento"] = method
        
        if method == 'pix':
            chave_pix = SecurityService.sanitize_input(payment_data.get('chave_pix'), 100)
            if not chave_pix:
                return {"valid": False, "error": "Chave PIX obrigatória"}
            
            # Validar formato básico de chave PIX
            pix_patterns = [
                r'^[0-9]{11}$',  # CPF
                r'^[0-9]{14}$',  # CNPJ
                r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',  # Email
                r'^\+?[0-9]{10,15}$'  # Telefone
            ]
            
            if not any(re.match(pattern, chave_pix.replace('.', '').replace('-', '')) for pattern in pix_patterns):
                return {"valid": False, "error": "Formato de chave PIX inválido"}
            
            result["sanitized_data"]["chave_pix"] = chave_pix
            
        elif method == 'transfer':
            banco = SecurityService.sanitize_input(payment_data.get('banco'), 50)
            agencia = SecurityService.sanitize_input(payment_data.get('agencia'), 20)
            conta = SecurityService.sanitize_input(payment_data.get('conta'), 20)
            tipo_conta = payment_data.get('tipo_conta')
            
            if not all([banco, agencia, conta, tipo_conta]):
                return {"valid": False, "error": "Dados bancários incompletos"}
            
            if tipo_conta not in ['corrente', 'poupanca']:
                return {"valid": False, "error": "Tipo de conta inválido"}
            
            result["sanitized_data"].update({
                "banco": banco,
                "agencia": agencia,
                "conta": conta,
                "tipo_conta": tipo_conta
            })
            
        elif method == 'skrill':
            carteira = SecurityService.sanitize_input(payment_data.get('carteira'), 100)
            if not carteira or '@' not in carteira:
                return {"valid": False, "error": "E-mail Skrill inválido"}
            
            # Validação básica de email
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, carteira):
                return {"valid": False, "error": "Formato de e-mail inválido"}
            
            result["sanitized_data"]["carteira"] = carteira
        
        return result
    
    @staticmethod
    def check_rate_limit(identifier: str, max_requests: int = 10, window_seconds: int = 60) -> bool:
        """
        Verifica rate limiting básico (em produção, usar Redis)
        """
        current_time = time.time()
        window_start = current_time - window_seconds
        
        # Limpar requests antigos
        SecurityService._rate_limit_storage[identifier] = [
            timestamp for timestamp in SecurityService._rate_limit_storage[identifier]
            if timestamp > window_start
        ]
        
        # Verificar se excedeu o limite
        if len(SecurityService._rate_limit_storage[identifier]) >= max_requests:
            logger.warning(f"Rate limit excedido para {identifier}")
            return False
        
        # Adicionar request atual
        SecurityService._rate_limit_storage[identifier].append(current_time)
        return True
    
    @staticmethod
    def get_client_identifier() -> str:
        """
        Obtém identificador único do cliente para rate limiting
        """
        # Em produção, considerar usar IP + User-Agent hash
        return request.remote_addr or 'unknown'
    
    @staticmethod
    def log_security_event(event_type: str, details: Dict[str, Any]):
        """
        Log de eventos de segurança
        """
        client_ip = request.remote_addr
        user_agent = request.headers.get('User-Agent', 'Unknown')
        
        log_data = {
            "event_type": event_type,
            "client_ip": client_ip,
            "user_agent": user_agent,
            "timestamp": time.time(),
            **details
        }
        
        logger.warning(f"SECURITY_EVENT: {log_data}")
        
        # Em produção, enviar para sistema de monitoramento
        if current_app:
            current_app.logger.warning(f"Security Event: {event_type} from {client_ip}")
