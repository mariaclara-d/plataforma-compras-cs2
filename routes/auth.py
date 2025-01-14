from flask import Blueprint, session, redirect, request, url_for
from urllib.parse import urlencode
import os
import requests

# Configuração do Blueprint para rotas de autenticação
auth_blueprint = Blueprint('auth', __name__) 

STEAM_OPENID_URL = "https://steamcommunity.com/openid/login"

# Rota para redirecionar o usuário ao Steam para login
@auth_blueprint.route("/login")
def steam_login():
    params = {
        'openid.ns': "http://specs.openid.net/auth/2.0",
        'openid.identity': "http://specs.openid.net/auth/2.0/identifier_select",
        'openid.claimed_id': "http://specs.openid.net/auth/2.0/identifier_select",
        'openid.mode': 'checkid_setup',
        'openid.return_to': os.getenv("STEAM_RETURN_URL").strip(),  # URL de retorno válida
        'openid.realm': os.getenv("STEAM_REALM").strip()           # URL base válida
    }
    query_string = urlencode(params)
    auth_url = STEAM_OPENID_URL + "?" + query_string
    return redirect(auth_url)

# Função para verificar a resposta do Steam após o login
def verify_steam_response(args):
    params = {
        'openid.assoc_handle': args.get('openid.assoc_handle'),
        'openid.signed': args.get('openid.signed'),
        'openid.sig': args.get('openid.sig'),
        'openid.ns': "http://specs.openid.net/auth/2.0",
        'openid.mode': 'check_authentication',
    }
    for item in args.get('openid.signed').split(','):
        params[f'openid.{item}'] = args.get(f'openid.{item}')

    response = requests.post(STEAM_OPENID_URL, data=params)
    return 'is_valid:true' in response.text

# Rota para processar o retorno do Steam e obter o Steam ID
@auth_blueprint.route("/complete_steam_login")
def complete_steam_login():
    openid_claimed_id = request.args.get('openid.claimed_id')
    if openid_claimed_id and verify_steam_response(request.args):
        steam_id = openid_claimed_id.split('/')[-1]
        session['steam_id'] = steam_id
        return redirect(url_for("dashboard.dashboard"))  # Redireciona para a dashboard após login
    print(steam_id)
    return "Erro ao verificar resposta do Steam", 400


