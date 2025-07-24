# routes/dashboard.py
from flask import Blueprint, session, redirect, url_for, render_template, jsonify, request
from routes.forms import TradeLinkForm 
from services.inventory_service import InventoryService
from services.saldo_service import calcular_saldo_usuario
import requests
import os
import logging
from dotenv import load_dotenv

load_dotenv()

dashboard_blueprint = Blueprint('dashboard', __name__, template_folder="../templates")

STEAM_API_KEY = os.getenv("STEAM_API_KEY")
inventory_service = InventoryService()

def get_steam_user_info(steam_id):
    url = f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/"
    params = {"key": STEAM_API_KEY, "steamids": steam_id}
    try:
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            players = data.get("response", {}).get("players", [])
            if players:
                return players[0]
    except requests.RequestException:
        pass
    return None

def parse_price(price_str):
    if price_str is None:
        return 0
    try:
        return float(price_str)
    except (ValueError, TypeError):
        return 0

@dashboard_blueprint.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "steam_id" not in session:
        return redirect(url_for("auth.steam_login"))

    user_steam_id = session["steam_id"]
    form = TradeLinkForm()
    inventory = []
    tradelink = None
    error = None
    percentual_comissao = 0.65

    user_info = get_steam_user_info(user_steam_id.replace("https://steamcommunity.com/openid/id/", ""))
    if not user_info:
        return redirect(url_for("auth.logout"))

    saldo = calcular_saldo_usuario(user_steam_id, percentual_comissao)

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
def api_saldo():
    if "steam_id" not in session:
        return jsonify({"erro": "Usuário não autenticado"}), 401
    
    user_steam_id = session["steam_id"]
    percentual_comissao = 0.65
    saldo = calcular_saldo_usuario(user_steam_id, percentual_comissao)
    return jsonify({"saldo": saldo})

@dashboard_blueprint.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home.home"))
