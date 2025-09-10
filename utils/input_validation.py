"""
Utilitários de validação e sanitização de input
Protege contra XSS, SQL Injection e outros ataques
"""
import re
import html
import urllib.parse
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from flask import request, jsonify
from functools import wraps

class InputValidator:
    """Classe para validação e sanitização de inputs"""
    
    # Regex patterns para validação
    STEAM_ID_PATTERN = re.compile(r'^765611[0-9]{11}$')  # Steam ID64 válido
    USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{3,20}$')
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    TRADELINK_PATTERN = re.compile(r'^https://steamcommunity\.com/tradeoffer/new/\?partner=\d+&token=[a-zA-Z0-9_-]+$')
    
    # Lista de palavras perigosas para SQL injection
    SQL_INJECTION_PATTERNS = [
        r'\b(union|select|insert|update|delete|drop|create|alter|exec|execute)\b',
        r'[\'";]',
        r'--',
        r'/\*.*\*/',
        r'\bor\s+1\s*=\s*1\b',
        r'\band\s+1\s*=\s*1\b'
    ]
    
    # Lista de tags perigosas para XSS
    XSS_PATTERNS = [
        r'<script[^>]*>.*?</script>',
        r'<iframe[^>]*>.*?</iframe>',
        r'<object[^>]*>.*?</object>',
        r'<embed[^>]*>',
        r'<link[^>]*>',
        r'<meta[^>]*>',
        r'javascript:',
        r'vbscript:',
        r'data:',
        r'on\w+\s*=',
    ]
    
    @staticmethod
    def sanitize_string(value: str, max_length: int = 255) -> str:
        """
        Sanitiza string removendo caracteres perigosos
        
        Args:
            value: String a ser sanitizada
            max_length: Comprimento máximo permitido
            
        Returns:
            String sanitizada
        """
        if not isinstance(value, str):
            return ""
        
        # Remover caracteres de controle
        value = ''.join(char for char in value if ord(char) >= 32 or char in '\t\n\r')
        
        # Escape HTML
        value = html.escape(value, quote=True)
        
        # Truncar se muito longo
        if len(value) > max_length:
            value = value[:max_length]
        
        return value.strip()
    
    @staticmethod
    def sanitize_html(value: str) -> str:
        """
        Remove tags HTML perigosas e JavaScript
        
        Args:
            value: HTML a ser sanitizado
            
        Returns:
            HTML sanitizado
        """
        if not isinstance(value, str):
            return ""
        
        # Remover padrões XSS
        for pattern in InputValidator.XSS_PATTERNS:
            value = re.sub(pattern, '', value, flags=re.IGNORECASE | re.DOTALL)
        
        # Escape HTML restante
        value = html.escape(value, quote=True)
        
        return value
    
    @staticmethod
    def validate_steam_id(steam_id: str) -> bool:
        """
        Valida Steam ID
        
        Args:
            steam_id: Steam ID para validar
            
        Returns:
            True se válido, False caso contrário
        """
        if not isinstance(steam_id, str):
            return False
        
        return bool(InputValidator.STEAM_ID_PATTERN.match(steam_id))
    
    @staticmethod
    def validate_username(username: str) -> bool:
        """
        Valida username
        
        Args:
            username: Username para validar
            
        Returns:
            True se válido, False caso contrário
        """
        if not isinstance(username, str):
            return False
        
        return bool(InputValidator.USERNAME_PATTERN.match(username))
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """
        Valida email
        
        Args:
            email: Email para validar
            
        Returns:
            True se válido, False caso contrário
        """
        if not isinstance(email, str):
            return False
        
        return bool(InputValidator.EMAIL_PATTERN.match(email))
    
    @staticmethod
    def validate_tradelink(tradelink: str) -> bool:
        """
        Valida trade link do Steam
        
        Args:
            tradelink: Trade link para validar
            
        Returns:
            True se válido, False caso contrário
        """
        if not isinstance(tradelink, str):
            return False
        
        return bool(InputValidator.TRADELINK_PATTERN.match(tradelink))
    
    @staticmethod
    def check_sql_injection(value: str) -> bool:
        """
        Verifica se há tentativas de SQL injection
        
        Args:
            value: String para verificar
            
        Returns:
            True se suspeito de SQL injection, False caso contrário
        """
        if not isinstance(value, str):
            return False
        
        value_lower = value.lower()
        
        for pattern in InputValidator.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value_lower, re.IGNORECASE):
                return True
        
        return False
    
    @staticmethod
    def validate_numeric(value: Any, min_val: float = None, max_val: float = None) -> bool:
        """
        Valida valor numérico
        
        Args:
            value: Valor para validar
            min_val: Valor mínimo permitido
            max_val: Valor máximo permitido
            
        Returns:
            True se válido, False caso contrário
        """
        try:
            num_val = float(value)
            
            if min_val is not None and num_val < min_val:
                return False
            
            if max_val is not None and num_val > max_val:
                return False
            
            return True
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def sanitize_json_input(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitiza input JSON recursivamente
        
        Args:
            data: Dicionário para sanitizar
            
        Returns:
            Dicionário sanitizado
        """
        if not isinstance(data, dict):
            return {}
        
        sanitized = {}
        
        for key, value in data.items():
            # Sanitizar chave
            clean_key = InputValidator.sanitize_string(str(key), 50)
            
            # Sanitizar valor baseado no tipo
            if isinstance(value, str):
                clean_value = InputValidator.sanitize_string(value)
            elif isinstance(value, dict):
                clean_value = InputValidator.sanitize_json_input(value)
            elif isinstance(value, list):
                clean_value = [
                    InputValidator.sanitize_string(str(item)) if isinstance(item, str) else item
                    for item in value[:100]  # Limitar tamanho da lista
                ]
            else:
                clean_value = value
            
            if clean_key:  # Apenas adicionar se a chave não estiver vazia
                sanitized[clean_key] = clean_value
        
        return sanitized

def validate_json_input(required_fields: List[str] = None, 
                       optional_fields: List[str] = None,
                       max_size: int = 1024) -> callable:
    """
    Decorator para validar input JSON
    
    Args:
        required_fields: Lista de campos obrigatórios
        optional_fields: Lista de campos opcionais
        max_size: Tamanho máximo do JSON em bytes
        
    Returns:
        Decorator function
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Verificar Content-Type
            if not request.is_json:
                return jsonify({'error': 'Content-Type deve ser application/json'}), 400
            
            # Verificar tamanho
            if request.content_length and request.content_length > max_size:
                return jsonify({'error': 'Payload muito grande'}), 413
            
            try:
                data = request.get_json()
                if not isinstance(data, dict):
                    return jsonify({'error': 'JSON deve ser um objeto'}), 400
            except Exception:
                return jsonify({'error': 'JSON inválido'}), 400
            
            # Sanitizar input
            data = InputValidator.sanitize_json_input(data)
            
            # Verificar campos obrigatórios
            if required_fields:
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    return jsonify({
                        'error': f'Campos obrigatórios ausentes: {", ".join(missing_fields)}'
                    }), 400
            
            # Verificar campos permitidos
            allowed_fields = (required_fields or []) + (optional_fields or [])
            if allowed_fields:
                invalid_fields = [field for field in data.keys() if field not in allowed_fields]
                if invalid_fields:
                    return jsonify({
                        'error': f'Campos não permitidos: {", ".join(invalid_fields)}'
                    }), 400
            
            # Verificar SQL injection em todos os valores string
            for key, value in data.items():
                if isinstance(value, str) and InputValidator.check_sql_injection(value):
                    return jsonify({'error': 'Input suspeito detectado'}), 400
            
            # Adicionar dados sanitizados à request
            request.validated_json = data
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def validate_form_input(required_fields: List[str] = None,
                       optional_fields: List[str] = None) -> callable:
    """
    Decorator para validar input de formulário
    
    Args:
        required_fields: Lista de campos obrigatórios
        optional_fields: Lista de campos opcionais
        
    Returns:
        Decorator function
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            data = {}
            
            # Coletar dados do formulário
            for field in (required_fields or []) + (optional_fields or []):
                value = request.form.get(field, '').strip()
                if value:
                    # Sanitizar valor
                    data[field] = InputValidator.sanitize_string(value)
            
            # Verificar campos obrigatórios
            if required_fields:
                missing_fields = [field for field in required_fields if not data.get(field)]
                if missing_fields:
                    return jsonify({
                        'error': f'Campos obrigatórios ausentes: {", ".join(missing_fields)}'
                    }), 400
            
            # Verificar SQL injection
            for key, value in data.items():
                if InputValidator.check_sql_injection(value):
                    return jsonify({'error': 'Input suspeito detectado'}), 400
            
            # Adicionar dados validados à request
            request.validated_form = data
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Funções de conveniência para validações específicas
def validate_steam_id_param(steam_id: str) -> bool:
    """Valida parâmetro Steam ID"""
    return InputValidator.validate_steam_id(steam_id)

def validate_asset_id(asset_id: str) -> bool:
    """Valida Asset ID"""
    return isinstance(asset_id, str) and asset_id.isdigit() and len(asset_id) <= 20

def validate_trade_offer_id(offer_id: str) -> bool:
    """Valida Trade Offer ID"""
    return isinstance(offer_id, str) and offer_id.isdigit() and len(offer_id) <= 20

def validate_amount(amount: Any) -> bool:
    """Valida valor monetário"""
    return InputValidator.validate_numeric(amount, min_val=0.01, max_val=99999.99)
