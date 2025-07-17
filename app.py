import logging

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
import os

# Cria instância global do CSRF
csrf = CSRFProtect()

def create_app():
    # Carrega o .env manualmente
    dotenv_path = Path("C:/Users/Tito el mestre/Documents/GitHub/documentacaoFlask---Copia/.env")
    load_dotenv(dotenv_path=dotenv_path)

    

    # Inicializa o app
    app = Flask(__name__)

    # Configurações essenciais
    app.config['SECRET_KEY'] = os.getenv("SECRET_KEY") or 'chave-padrao'
    app.config['STEAM_API_KEY_NAO_OFICIAL'] = os.getenv("STEAM_API_KEY_NAO_OFICIAL")
    app.config['STEAM_API_KEY'] = os.getenv("STEAM_API_KEY")
    app.config['STEAM_RETURN_URL'] = os.getenv("STEAM_RETURN_URL")
    app.config['STEAM_REALM'] = os.getenv("STEAM_REALM")
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("SQLALCHEMY_DATABASE_URI")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Inicializa CSRF
    csrf.init_app(app)

    # Injeta token CSRF para uso em <input id="csrf_token"> no base.html
    @app.context_processor
    def inject_csrf_token():
        token = generate_csrf()
        return dict(csrf_token=token)

    # Inicializa banco e migrações
    db.init_app(app)
    migrate = Migrate(app, db)

    # Blueprints
    from routes.home import home_blueprint
    from routes.auth import auth_blueprint
    from routes.dashboard import dashboard_blueprint
    from routes.forms import forms_blueprint
    from routes.inventory import inventory_blueprint
    from routes.trade import trade_blueprint
    from routes.offer import offer_blueprint

    app.register_blueprint(home_blueprint)
    app.register_blueprint(auth_blueprint)
    app.register_blueprint(dashboard_blueprint)
    app.register_blueprint(forms_blueprint, url_prefix='/forms')
    app.register_blueprint(inventory_blueprint, url_prefix='/inventory')
    app.register_blueprint(trade_blueprint, url_prefix='/trade')
    app.register_blueprint(offer_blueprint, url_prefix='/offer')

    return app








