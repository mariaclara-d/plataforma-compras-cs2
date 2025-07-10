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
    steam_return_url = os.getenv("STEAM_RETURN_URL")
    steam_realm = os.getenv("STEAM_REALM")
    if not steam_return_url or not steam_realm:
        return "Configuração de autenticação Steam ausente.", 500
    params = {
        'openid.ns': "http://specs.openid.net/auth/2.0",
        'openid.identity': "http://specs.openid.net/auth/2.0/identifier_select",
        'openid.claimed_id': "http://specs.openid.net/auth/2.0/identifier_select",
        'openid.mode': 'checkid_setup',
        'openid.return_to': steam_return_url.strip(),
        'openid.realm': steam_realm.strip()
    }
    query_string = urlencode(params)
    auth_url = STEAM_OPENID_URL + "?" + query_string
    return redirect(auth_url)

# Função para verificar a resposta do Steam após o login
def verify_steam_response(args):
    try:
        signed = args.get('openid.signed')
        if not signed:
            return False
        params = {
            'openid.assoc_handle': args.get('openid.assoc_handle'),
            'openid.signed': signed,
            'openid.sig': args.get('openid.sig'),
            'openid.ns': "http://specs.openid.net/auth/2.0",
            'openid.mode': 'check_authentication',
        }
        for item in signed.split(','):
            params[f'openid.{item}'] = args.get(f'openid.{item}')
        response = requests.post(STEAM_OPENID_URL, data=params, timeout=5)
        return 'is_valid:true' in response.text
    except Exception:
        return False

# Rota para processar o retorno do Steam e obter o Steam ID
@auth_blueprint.route("/complete_steam_login")
def complete_steam_login():
    openid_claimed_id = request.args.get('openid.claimed_id')
    if openid_claimed_id and verify_steam_response(request.args):
        steam_id = openid_claimed_id.split('/')[-1]
        # Validação básica do steam_id
        if not steam_id.isdigit() or len(steam_id) > 20:
            return "Steam ID inválido.", 400
        session['steam_id'] = steam_id
        return redirect(url_for("dashboard.dashboard"))  # Redireciona para a dashboard após login
    return "Erro ao verificar resposta do Steam", 400


