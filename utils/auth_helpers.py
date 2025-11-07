# utils/auth_helpers.py
"""
Utilitários de autenticação e validação de sessão
"""
from flask import session, request, abort, current_app
from functools import wraps
import time
import hmac
import hashlib
import os

def generate_session_token(steam_id):
    """Gera token de sessão seguro"""
    timestamp = str(int(time.time()))
    data = f"{steam_id}:{timestamp}"
    secret = current_app.config['SECRET_KEY'].encode()
    token = hmac.new(secret, data.encode(), hashlib.sha256).hexdigest()
    return f"{timestamp}:{token}"

def validate_session_token(steam_id, token):
    """Valida token de sessão"""
    if not token or ':' not in token:
        return False
    
    try:
        timestamp, received_token = token.split(':', 1)
        
        # Verificar se token não expirou (24 horas)
        if int(time.time()) - int(timestamp) > 86400:
            return False
        
        # Regenerar token esperado
        data = f"{steam_id}:{timestamp}"
        secret = current_app.config['SECRET_KEY'].encode()
        expected_token = hmac.new(secret, data.encode(), hashlib.sha256).hexdigest()
        
        # Comparação segura contra timing attacks
        return hmac.compare_digest(received_token, expected_token)
        
    except (ValueError, TypeError):
        return False

def validate_steam_id(steam_id):
    """Valida formato do Steam ID"""
    if not steam_id or not isinstance(steam_id, str):
        return False
    
    # Steam ID deve ser numérico e ter 17 dígitos
    if not steam_id.isdigit() or len(steam_id) != 17:
        return False
    
    # Steam ID deve começar com 76561 (formato Steam64)
    if not steam_id.startswith('76561'):
        return False
    
    # Verificar se é um Steam ID válido (range básico)
    steam_id_int = int(steam_id)
    if steam_id_int < 76561197960265728 or steam_id_int > 76561999999999999:
        return False
    
    return True

def require_auth(f):
    """Decorator para exigir autenticação válida"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Verificar se existe steam_id na sessão
        steam_id = session.get('steam_id')
        if not steam_id:
            current_app.logger.warning(f"Acesso não autorizado tentativa: {request.remote_addr}")
            abort(401)
        
        # Validar formato do Steam ID
        if not validate_steam_id(steam_id):
            current_app.logger.warning(f"Steam ID inválido na sessão: {steam_id}")
            session.clear()
            abort(401)
        
        # Validar token de sessão
        session_token = session.get('session_token')
        if not validate_session_token(steam_id, session_token):
            current_app.logger.warning(f"Token de sessão inválido: {request.remote_addr}")
            session.clear()
            abort(401)
        
        return f(*args, **kwargs)
    
    return decorated_function

def create_secure_session(steam_id):
    """Cria sessão segura após autenticação bem-sucedida"""
    if not validate_steam_id(steam_id):
        raise ValueError("Steam ID inválido")
    
    # Regenerar session ID para prevenir session fixation
    session.permanent = True
    session['steam_id'] = steam_id
    session['session_token'] = generate_session_token(steam_id)
    session['created_at'] = int(time.time())
    session['ip_address'] = request.remote_addr
    
    current_app.logger.info(f"Sessão segura criada para Steam ID: {steam_id}")

def validate_session_integrity():
    """Valida integridade da sessão atual"""
    # Verificar se IP mudou (opcional - pode ser muito restritivo)
    if current_app.config.get('VALIDATE_SESSION_IP', False):
        if session.get('ip_address') != request.remote_addr:
            current_app.logger.warning(f"IP da sessão mudou: {session.get('ip_address')} -> {request.remote_addr}")
            session.clear()
            return False
    
    return True

def clear_session():
    """Limpa sessão de forma segura"""
    session.clear()
    current_app.logger.info("Sessão limpa com sucesso")
