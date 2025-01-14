from flask import Flask
from routes.home import home_blueprint
from routes.auth import auth_blueprint
from routes.dashboard import dashboard_blueprint
from routes.forms import forms_blueprint
from routes.inventory import inventory_blueprint
from routes.trade import trade_blueprint
from dotenv import load_dotenv
import os 

load_dotenv()


# Inicialização do Flask
app = Flask(__name__)

app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
app.config['STEAM_API_KEY_NAO_OFICIAL']=os.getenv("STEAM_API_KEY_NAO_OFICIAL")
app.config['STEAM_API_KEY']=os.getenv("STEAM_API_KEY")
app.config['STEAM_RETURN_URL']=os.getenv("STEAM_RETURN_URL")
app.config['STEAM_REALM']=os.getenv("STEAM_REALM")

# Registro de blueprints
app.register_blueprint(home_blueprint)
app.register_blueprint(auth_blueprint)
app.register_blueprint(dashboard_blueprint)

app.register_blueprint(forms_blueprint, url_prefix='/forms')
app.register_blueprint(inventory_blueprint, url_prefix='/inventory')
app.register_blueprint(trade_blueprint, url_prefix='/trade')


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)











