from flask import Blueprint, render_template, request, current_app

home_blueprint = Blueprint('home', __name__)

@home_blueprint.route('/')
def home():
    current_app.logger.info(f"Acesso à home de {request.remote_addr}")
    return render_template('index.html')