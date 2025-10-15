# routes/dashboard.py
from flask import Blueprint, session, redirect, url_for, render_template, jsonify, request
from routes.forms import TradeLinkForm 
from services.inventory_service import InventoryService
from decimal import Decimal, InvalidOperation
from services.saldo_service import calcular_saldo_usuario
from utils.auth_helpers import require_auth
import requests
import os
import logging
from dotenv import load_dotenv

load_dotenv()

dashboard_blueprint = Blueprint('dashboard', __name__, template_folder="../templates")

STEAM_API_KEY = os.getenv("STEAM_API_KEY")
inventory_service = InventoryService()

def get_steam_user_info(steam_id):
    """Busca informações do usuário Steam com tratamento de erro melhorado"""
    url = f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/"
    params = {"key": STEAM_API_KEY, "steamids": steam_id}
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()  # Levanta exceção para status HTTP de erro
        
        if response.status_code == 200:
            data = response.json()
            players = data.get("response", {}).get("players", [])
            if players:
                logging.info(f"[DASHBOARD] Informações do usuário Steam obtidas com sucesso: {steam_id}")
                return players[0]
            else:
                logging.warning(f"[DASHBOARD] Nenhum jogador encontrado para Steam ID: {steam_id}")
                
    except requests.exceptions.Timeout:
        logging.error(f"[DASHBOARD] Timeout ao buscar informações do usuário Steam: {steam_id}")
    except requests.exceptions.RequestException as e:
        logging.error(f"[DASHBOARD] Erro na requisição Steam API: {str(e)}")
    except Exception as e:
        logging.error(f"[DASHBOARD] Erro inesperado ao buscar usuário Steam: {str(e)}")
        
    return None

def parse_price(price_str):
    if price_str is None:
        return Decimal('0.00')
    try:
        return Decimal(price_str)
    except (ValueError, TypeError, InvalidOperation):
        return Decimal('0.00')

@dashboard_blueprint.route("/dashboard", methods=["GET", "POST"])
@require_auth
def dashboard():

    user_steam_id = session["steam_id"]
    form = TradeLinkForm()
    inventory = []
    tradelink = None
    error = None
    percentual_comissao = 0.65

    user_info = get_steam_user_info(user_steam_id.replace("https://steamcommunity.com/openid/id/", ""))
    if not user_info:
        return redirect(url_for("auth.logout"))

    saldo = calcular_saldo_usuario(user_steam_id)

    if form.validate_on_submit():
        tradelink = form.tradelink.data
        result = inventory_service.fetch_inventory(tradelink, user_steam_id)
        
        if isinstance(result, tuple) and result[1] == 400:
            error = result[0]["error"]
        else:
            inventory = sorted(
                result.get("inventory", []),
                key=lambda x: parse_price(x.get("price_median")),
                reverse=True
            )
            logging.info(f"[DASHBOARD] Inventário ordenado e pronto para exibição - {len(inventory)} itens")

    return render_template(
        "dashboard.html",
        form=form,
        inventory=inventory,
        tradelink=tradelink,
        error=error,
        user_info=user_info,
        saldo=saldo
    )
    
@dashboard_blueprint.route("/api/saldo")
@require_auth
def api_saldo():
    user_steam_id = session["steam_id"]
    saldo = calcular_saldo_usuario(user_steam_id)
    return jsonify({"saldo": saldo})

@dashboard_blueprint.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home.home"))
