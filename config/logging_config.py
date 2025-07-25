# config/logging_config.py
import logging
import logging.handlers
import os
from datetime import datetime

def setup_security_logging():
    """Configura logging de segurança para a aplicação"""
    
    # Criar diretório de logs se não existir
    log_dir = os.path.join(os.getcwd(), 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Configurar logger de segurança
    security_logger = logging.getLogger('security')
    security_logger.setLevel(logging.INFO)
    
    # Formatter para logs de segurança
    security_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler para arquivo de segurança (rotativo)
    security_file_handler = logging.handlers.RotatingFileHandler(
        os.path.join(log_dir, 'security.log'),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    security_file_handler.setLevel(logging.INFO)
    security_file_handler.setFormatter(security_formatter)
    
    # Handler para console (apenas em desenvolvimento)
    if os.getenv('FLASK_ENV') != 'production':
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(security_formatter)
        security_logger.addHandler(console_handler)
    
    security_logger.addHandler(security_file_handler)
    
    # Configurar logger geral da aplicação
    app_logger = logging.getLogger('app')
    app_logger.setLevel(logging.INFO)
    
    app_formatter = logging.Formatter(
        '%(asctime)s | %(levelname)s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler para arquivo da aplicação
    app_file_handler = logging.handlers.RotatingFileHandler(
        os.path.join(log_dir, 'app.log'),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    app_file_handler.setLevel(logging.INFO)
    app_file_handler.setFormatter(app_formatter)
    app_logger.addHandler(app_file_handler)
    
    # Handler para erros críticos
    error_file_handler = logging.handlers.RotatingFileHandler(
        os.path.join(log_dir, 'error.log'),
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3
    )
    error_file_handler.setLevel(logging.ERROR)
    error_file_handler.setFormatter(app_formatter)
    app_logger.addHandler(error_file_handler)
    
    return security_logger, app_logger

def log_security_event(event_type: str, details: dict, level: str = 'WARNING'):
    """Função auxiliar para logar eventos de segurança"""
    security_logger = logging.getLogger('security')
    
    log_message = f"SECURITY_EVENT: {event_type} | {details}"
    
    if level == 'INFO':
        security_logger.info(log_message)
    elif level == 'WARNING':
        security_logger.warning(log_message)
    elif level == 'ERROR':
        security_logger.error(log_message)
    elif level == 'CRITICAL':
        security_logger.critical(log_message)

# Lista de eventos de segurança monitorados
SECURITY_EVENTS = {
    'LOGIN_SUCCESS': 'Login realizado com sucesso',
    'LOGIN_FAILED': 'Tentativa de login falhada',
    'CSRF_INVALID': 'Token CSRF inválido',
    'RATE_LIMIT_EXCEEDED': 'Rate limit excedido',
    'INVALID_STEAM_ID': 'SteamID inválido fornecido',
    'INVALID_TRADELINK': 'Trade link inválido',
    'UNAUTHORIZED_TRADE': 'Tentativa de trade não autorizado',
    'INVALID_ASSETID': 'Asset ID inválido',
    'INVALID_PAYMENT_DATA': 'Dados de pagamento inválidos',
    'INVALID_ITEMS_SELECTED': 'Itens inválidos selecionados',
    'INVALID_REQUEST_DATA': 'Dados de requisição inválidos',
    'SQL_INJECTION_ATTEMPT': 'Tentativa de SQL Injection detectada',
    'XSS_ATTEMPT': 'Tentativa de XSS detectada',
    'SUSPICIOUS_ACTIVITY': 'Atividade suspeita detectada'
}
