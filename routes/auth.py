from flask import Blueprint, session, redirect, request, url_for, current_app, abort
from urllib.parse import urlencode
import os
import requests
import re
from utils.auth_helpers import create_secure_session, validate_steam_id, clear_session

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
    try:
        openid_claimed_id = request.args.get('openid.claimed_id')
        current_app.logger.info(f"Tentativa de login Steam de IP: {request.remote_addr}")
        
        if not openid_claimed_id:
            current_app.logger.warning("Login Steam sem openid.claimed_id")
            abort(400)
        
        # Validar formato do claimed_id
        if not openid_claimed_id.startswith('https://steamcommunity.com/openid/id/'):
            current_app.logger.warning(f"Formato inválido de claimed_id: {openid_claimed_id}")
            abort(400)
        
        if not verify_steam_response(request.args):
            current_app.logger.warning("Falha na verificação da resposta Steam")
            abort(400)
        
        # Extrair Steam ID de forma segura
        steam_id = openid_claimed_id.split('/')[-1]
        
        # Validar Steam ID
        if not validate_steam_id(steam_id):
            current_app.logger.warning(f"Steam ID inválido extraído: {steam_id}")
            abort(400)
        
        # Criar sessão segura
        create_secure_session(steam_id)
        
        current_app.logger.info(f"Login Steam bem-sucedido para Steam ID: {steam_id}")
        return redirect(url_for("dashboard.dashboard"))
        
    except Exception as e:
        current_app.logger.error(f"Erro no login Steam: {str(e)}")
        abort(500)

@auth_blueprint.route("/logout")
def logout():
    """Logout seguro"""
    current_app.logger.info(f"Logout realizado por IP: {request.remote_addr}")
    clear_session()
    return redirect(url_for("home.home"))


