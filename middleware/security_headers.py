# middleware/security_headers.py
from flask import current_app, request
import re

class SecurityHeadersMiddleware:
    """Middleware para adicionar cabeçalhos de segurança"""
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        app.after_request(self.add_security_headers)
    
    def add_security_headers(self, response):
        """Adiciona cabeçalhos de segurança a todas as respostas"""
        
        # Configurar CSP (Content Security Policy)
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://stackpath.bootstrapcdn.com",
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com",
            "font-src 'self' https://fonts.gstatic.com",
            "img-src 'self' data: https: http:",
            "connect-src 'self' https://api.steampowered.com https://steamcommunity.com https://www.steamwebapi.com",
            "frame-ancestors 'none'",
            "form-action 'self'",
            "base-uri 'self'"
        ]
        response.headers['Content-Security-Policy'] = '; '.join(csp_directives)
        
        # Prevenir clickjacking
        response.headers['X-Frame-Options'] = 'DENY'
        
        # Prevenir MIME sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'
        
        # XSS Protection
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # HTTPS Strict Transport Security (apenas em produção)
        if current_app.config.get('ENV') == 'production':
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        # Referrer Policy
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Feature Policy
        response.headers['Permissions-Policy'] = (
            "geolocation=(), microphone=(), camera=(), "
            "magnetometer=(), gyroscope=(), speaker=(), "
            "notifications=(), push=(), vibrate=()"
        )
        
        # Cache Control para páginas sensíveis
        if request.endpoint in ['auth.steam_login', 'dashboard.dashboard', 'admin.dashboard']:
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
        
        return response

def is_safe_url(target):
    """Verifica se uma URL de redirecionamento é segura"""
    ref_url = request.host_url
    test_url = target or '/'
    return test_url.startswith('/') or test_url.startswith(ref_url)

def sanitize_filename(filename):
    """Sanitiza nomes de arquivo para evitar path traversal"""
    # Remove caracteres perigosos
    filename = re.sub(r'[^\w\s-.]', '', filename)
    # Remove múltiplos pontos consecutivos
    filename = re.sub(r'\.{2,}', '.', filename)
    # Remove barras
    filename = filename.replace('/', '').replace('\\', '')
    return filename[:255]  # Limitar tamanho
