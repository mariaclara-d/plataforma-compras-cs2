from flask import session, redirect, request
from urllib.parse import urlencode
from urllib import parse
import os
import requests

STEAM_OPENID_URL = "https://steamcommunity.com/openid/login"

# Função para redirecionar o usuário ao Steam para login
def steam_login():
    params = {
        'openid.ns': "http://specs.openid.net/auth/2.0",
        'openid.identity': "http://specs.openid.net/auth/2.0/identifier_select",
        'openid.claimed_id': "http://specs.openid.net/auth/2.0/identifier_select",
        'openid.mode': 'checkid_setup',
        'openid.return_to': os.getenv("STEAM_RETURN_URL").strip(),  # URL de retorno válida
        'openid.realm': os.getenv("STEAM_REALM").strip()           # URL base válida
    }
    query_string = parse.urlencode(params)
    auth_url = STEAM_OPENID_URL + "?" + query_string
    print(auth_url)
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
    print("Resposta do Steam:", response.text)  # Para debug
    return 'is_valid:true' in response.text


# Função para processar o retorno do Steam e obter o Steam ID
def complete_steam_login():
    print("Parâmetros recebidos:", request.args)  # Para debug
    openid_claimed_id = request.args.get('openid.claimed_id')
    if openid_claimed_id and verify_steam_response(request.args):
        steam_id = openid_claimed_id.split('/')[-1]
        session['steam_id'] = steam_id
        print(f"Steam ID extraído: {steam_id}")
        return steam_id
    print("Erro ao verificar resposta do Steam")
    return None