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
    print(f"[LOG] STEAM_RETURN_URL: {steam_return_url}")
    print(f"[LOG] STEAM_REALM: {steam_realm}")
    if not steam_return_url or not steam_realm:
        print("[LOG] Configuração de autenticação Steam ausente.")
        return "Configuração de autenticação Steam ausente.", 500
    params = {
        'openid.ns': "http://specs.openid.net/auth/2.0",
        'openid.identity': "http://specs.openid.net/auth/2.0/identifier_select",
        'openid.claimed_id': "http://specs.openid.net/auth/2.0/identifier_select",
        'openid.mode': 'checkid_setup',
        'openid.return_to': steam_return_url.strip(),
        'openid.realm': steam_realm.strip()
    }
    print(f"[LOG] Parâmetros OpenID: {params}")
    query_string = urlencode(params)
    auth_url = STEAM_OPENID_URL + "?" + query_string
    print(f"[LOG] URL de autenticação Steam: {auth_url}")
    return redirect(auth_url)

# Função para verificar a resposta do Steam após o login
def verify_steam_response(args):
    try:
        signed = args.get('openid.signed')
        print(f"[LOG] Parâmetros recebidos do Steam: {args}")
        if not signed:
            print("[LOG] 'openid.signed' não encontrado na resposta.")
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
        print(f"[LOG] Parâmetros enviados para verificação: {params}")
        response = requests.post(STEAM_OPENID_URL, data=params, timeout=5)
        print(f"[LOG] Resposta da Steam: {response.text}")
        return 'is_valid:true' in response.text
    except Exception as e:
        print(f"[LOG] Erro na verificação da resposta do Steam: {e}")
        return False

# Rota para processar o retorno do Steam e obter o Steam ID
@auth_blueprint.route("/complete_steam_login")
def complete_steam_login():
    openid_claimed_id = request.args.get('openid.claimed_id')
    print(f"[LOG] openid.claimed_id recebido: {openid_claimed_id}")
    if openid_claimed_id and verify_steam_response(request.args):
        steam_id = openid_claimed_id.split('/')[-1]
        print(f"[LOG] Steam ID extraído: {steam_id}")
        # Validação básica do steam_id
        if not steam_id.isdigit() or len(steam_id) > 20:
            print("[LOG] Steam ID inválido.")
            return "Steam ID inválido.", 400
        session['steam_id'] = steam_id
        print("[LOG] Login Steam bem-sucedido, redirecionando para dashboard.")
        return redirect(url_for("dashboard.dashboard"))  # Redireciona para a dashboard após login
    print("[LOG] Erro ao verificar resposta do Steam")
    return "Erro ao verificar resposta do Steam", 400


