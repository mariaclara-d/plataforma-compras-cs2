# routes/dashboard.py
from flask import Blueprint, session, redirect, url_for, render_template
from routes.forms import TradeLinkForm 
from routes.inventory import fetch_inventory
from services.saldo_service import calcular_saldo_usuario
import requests
import os
from dotenv import load_dotenv

load_dotenv()

dashboard_blueprint = Blueprint('dashboard', __name__, template_folder="../templates")

STEAM_API_KEY = os.getenv("STEAM_API_KEY")

def get_steam_user_info(steam_id):
    url = f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/"
    params = {"key": STEAM_API_KEY, "steamids": steam_id}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        players = data.get("response", {}).get("players", [])
        if players:
            return players[0]
    return None

def parse_price(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0

@dashboard_blueprint.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "steam_id" not in session:
        return redirect(url_for("home"))

    user_steam_id = session["steam_id"]
    user_info = get_steam_user_info(user_steam_id)
    if not user_info:
        return redirect(url_for("dashboard.logout"))

    form = TradeLinkForm()
    tradelink = None
    inventory = []
    percentual_comissao = 0.10
    saldo = calcular_saldo_usuario(user_steam_id, percentual_comissao)

    if form.validate_on_submit():
        tradelink = form.tradelink.data
        result = fetch_inventory(tradelink, user_steam_id)

        if "error" in result:
            return render_template(
                "dashboard.html",
                form=form,
                error=result["error"],
                inventory=[],
                tradelink=tradelink,
                user_info=user_info,
                saldo=saldo
            )

        inventory = sorted(
            result.get("inventory", []),
            key=lambda x: parse_price(x.get("price_median")),
            reverse=True
        )

        return render_template(
            "dashboard.html",
            form=form,
            inventory=inventory,
            tradelink=tradelink,
            error=None if inventory else "Seu inventário está vazio.",
            user_info=user_info,
            saldo=saldo
        )

    return render_template(
        "dashboard.html",
        form=form,
        inventory=inventory,
        tradelink=tradelink,
        error=None,
        user_info=user_info,
        saldo=saldo
    )


@dashboard_blueprint.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home.home"))
