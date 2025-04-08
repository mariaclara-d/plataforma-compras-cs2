from flask import Flask
from db_config import db
from flask_migrate import Migrate
from dotenv import load_dotenv
from pathlib import Path
import os


def create_app():

    dotenv_path = Path("C:/Users/Tito el mestre/Documents/GitHub/documentacaoFlask---Copia/.env")
    load_dotenv(dotenv_path=dotenv_path)
    
    print("STEAM_USERNAME:", os.getenv("STEAM_USERNAME"))
    print("STEAM_PASSWORD:", os.getenv("STEAM_PASSWORD"))
    print("STEAM_SHARED_SECRET:", os.getenv("STEAM_SHARED_SECRET"))
    print("STEAM_API_KEY:", os.getenv("STEAM_API_KEY"))
    print("STEAM_GUARD_FILE:", os.getenv("STEAM_GUARD_FILE"))


    app = Flask(__name__)

    app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
    app.config['STEAM_API_KEY_NAO_OFICIAL'] = os.getenv("STEAM_API_KEY_NAO_OFICIAL")
    app.config['STEAM_API_KEY'] = os.getenv("STEAM_API_KEY")
    app.config['STEAM_RETURN_URL'] = os.getenv("STEAM_RETURN_URL")
    app.config['STEAM_REALM'] = os.getenv("STEAM_REALM")
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("SQLALCHEMY_DATABASE_URI")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    from routes.home import home_blueprint
    from routes.auth import auth_blueprint
    from routes.dashboard import dashboard_blueprint
    from routes.forms import forms_blueprint
    from routes.inventory import inventory_blueprint
    from routes.trade import trade_blueprint
    from routes.offer import offer_blueprint

    db.init_app(app)
    
    migrate = Migrate(app, db)

    app.register_blueprint(home_blueprint)
    app.register_blueprint(auth_blueprint)
    app.register_blueprint(dashboard_blueprint)
    app.register_blueprint(forms_blueprint, url_prefix='/forms')
    app.register_blueprint(inventory_blueprint, url_prefix='/inventory')
    app.register_blueprint(trade_blueprint, url_prefix='/trade')
    app.register_blueprint(offer_blueprint, url_prefix='/offer')

    return app








