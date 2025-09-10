# middleware/rate_limiting.py
"""
Middleware de Rate Limiting para proteção contra abuse
"""
from flask import request, jsonify, current_app
from functools import wraps
import time
from collections import defaultdict
import threading

class RateLimiter:
    """Rate limiter thread-safe usando sliding window"""
    
    def __init__(self):
        self.requests = defaultdict(list)
        self.lock = threading.Lock()
    
    def is_allowed(self, key, limit, window_seconds):
        """
        Verifica se request é permitido
        
        Args:
            key: Identificador único (IP, user_id, etc)
            limit: Número máximo de requests
            window_seconds: Janela de tempo em segundos
        """
        now = time.time()
        
        with self.lock:
            # Remove requests antigos
            self.requests[key] = [
                req_time for req_time in self.requests[key]
                if now - req_time < window_seconds
            ]
            
            # Verifica se pode fazer nova request
            if len(self.requests[key]) >= limit:
                return False
            
            # Adiciona nova request
            self.requests[key].append(now)
            return True
    
    def get_remaining(self, key, limit, window_seconds):
        """Retorna número de requests restantes"""
        now = time.time()
        
        with self.lock:
            recent_requests = [
                req_time for req_time in self.requests[key]
                if now - req_time < window_seconds
            ]
            return max(0, limit - len(recent_requests))

# Instância global do rate limiter
rate_limiter = RateLimiter()

def rate_limit(limit=100, window=3600, per="ip", message=None):
    """
    Decorator para rate limiting
    
    Args:
        limit: Número máximo de requests
        window: Janela de tempo em segundos
        per: Tipo de identificação ('ip', 'user', 'endpoint')
        message: Mensagem customizada de erro
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Determinar chave de identificação
            if per == "ip":
                key = f"ip:{request.remote_addr}"
            elif per == "user" and "steam_id" in request.get_json(silent=True) or {}:
                key = f"user:{request.get_json()['steam_id']}"
            elif per == "endpoint":
                key = f"endpoint:{request.endpoint}:{request.remote_addr}"
            else:
                key = f"ip:{request.remote_addr}"
            
            # Verificar rate limit
            if not rate_limiter.is_allowed(key, limit, window):
                current_app.logger.warning(
                    f"Rate limit exceeded for {key}: {limit}/{window}s"
                )
                
                error_message = message or f"Rate limit exceeded. Max {limit} requests per {window} seconds."
                return jsonify({"error": error_message}), 429
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

# Rate limiters específicos para diferentes endpoints
def admin_rate_limit(f):
    """Rate limiting para endpoints admin"""
    return rate_limit(limit=10, window=300, per="ip", 
                     message="Too many admin attempts. Try again in 5 minutes.")(f)

def api_rate_limit(f):
    """Rate limiting para APIs"""
    return rate_limit(limit=100, window=3600, per="ip",
                     message="API rate limit exceeded. Try again later.")(f)

def login_rate_limit(f):
    """Rate limiting para login"""
    return rate_limit(limit=5, window=300, per="ip",
                     message="Too many login attempts. Try again in 5 minutes.")(f)

def trade_rate_limit(f):
    """Rate limiting para trades"""
    return rate_limit(limit=10, window=600, per="user",
                     message="Too many trade attempts. Wait 10 minutes.")(f)
