import logging

# Configurar logging básico primeiro
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s"
)

from flask import Flask, session
from db_config import db
from flask_migrate import Migrate
from dotenv import load_dotenv
from pathlib import Path
from models import InformacoesPagamento, Skin, TradeOffer, Transacao, Saldo
from flask_wtf import CSRFProtect
from flask_wtf.csrf import generate_csrf
from config.logging_config import setup_security_logging
from middleware.security_headers import SecurityHeadersMiddleware
import os

# Configurar logging de segurança
setup_security_logging()

# Cria instância global do CSRF
csrf = CSRFProtect()

def create_app():
    # Carrega o .env manualmente
    dotenv_path = Path("c:/Users/Windows 10/Documents/GitHub/documentacaoFlask---Copia/.env")
    load_dotenv(dotenv_path=dotenv_path)

    # Inicializa o app
    app = Flask(__name__)

    # Configurações essenciais de segurança
    secret_key = os.getenv("SECRET_KEY")
    if not secret_key:
        if os.getenv("FLASK_ENV") == "production":
            raise ValueError("SECRET_KEY é obrigatória em produção. Defina uma chave forte no ambiente.")
        else:
            # Apenas para desenvolvimento - gerar chave aleatória
            import secrets
            secret_key = secrets.token_urlsafe(32)
            print("⚠️  AVISO: Usando SECRET_KEY temporária para desenvolvimento")
    
    app.config['SECRET_KEY'] = secret_key
    app.config['STEAM_API_KEY_NAO_OFICIAL'] = os.getenv("STEAM_API_KEY_NAO_OFICIAL")
    app.config['STEAM_API_KEY'] = os.getenv("STEAM_API_KEY")
    app.config['STEAM_RETURN_URL'] = os.getenv("STEAM_RETURN_URL")
    app.config['STEAM_REALM'] = os.getenv("STEAM_REALM")
    
    # Configurar banco de dados (SQLite ou PostgreSQL automaticamente)
    from db_config import configure_database
    database_url = configure_database(app)

    # Inicializa CSRF
    csrf.init_app(app)
    
    # Inicializa middleware de segurança
    SecurityHeadersMiddleware(app)

    # Injeta token CSRF para uso em <input id="csrf_token"> no base.html
    @app.context_processor
    def inject_csrf_token():
        token = generate_csrf()
        return dict(csrf_token=token)

    # Migrações (db já inicializado em configure_database)
    migrate = Migrate(app, db)

    # Blueprints
    from routes.home import home_blueprint
    from routes.auth import auth_blueprint
    from routes.dashboard import dashboard_blueprint
    from routes.forms import forms_blueprint
    from routes.inventory import inventory_blueprint
    from routes.trade import trade_blueprint
    from routes.offer import offer_blueprint
    from routes.admin import admin_bp
    from routes.saque import bp as saque_bp
    from routes.trade_holds import bp as trade_holds_bp
    from routes.transactions import transactions_blueprint

    app.register_blueprint(home_blueprint)
    app.register_blueprint(auth_blueprint)
    app.register_blueprint(dashboard_blueprint)
    app.register_blueprint(forms_blueprint, url_prefix='/forms')
    app.register_blueprint(inventory_blueprint, url_prefix='/inventory')
    app.register_blueprint(trade_blueprint, url_prefix='/trade')
    app.register_blueprint(offer_blueprint, url_prefix='/offer')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(saque_bp, url_prefix='/api')
    app.register_blueprint(trade_holds_bp)
    app.register_blueprint(transactions_blueprint)
    
    # Importar e registrar rota de status da Steam
    from routes.steam_status import bp as steam_status_bp
    app.register_blueprint(steam_status_bp)

    return app

if __name__ == '__main__':
    import sys
    
    app = create_app()
    
    # Configurações para staging/produção
    port = 5000
    host = "127.0.0.1"
    
    # Parse argumentos de linha de comando para staging
    for arg in sys.argv[1:]:
        if arg.startswith('--port='):
            port = int(arg.split('=')[1])
        elif arg.startswith('--host='):
            host = arg.split('=')[1]
    
    # Log de inicialização
    env_mode = os.getenv('FLASK_ENV', 'development')
    print(f"🚀 Iniciando aplicação em modo: {env_mode}")
    print(f"📍 URL: http://{host}:{port}")
    
    if env_mode == 'staging':
        print("🧪 AMBIENTE DE STAGING ATIVO")
        print("📊 Logs disponíveis em: ./logs/")
        print("🔒 Segurança: Rate limiting e validações ativas")
    
    app.run(debug=(env_mode == 'development'), host=host, port=port)








