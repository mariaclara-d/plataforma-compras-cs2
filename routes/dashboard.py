from flask import Blueprint, session, redirect, url_for, render_template
from routes.forms import TradeLinkForm 
from routes.inventory import fetch_inventory
import requests
import os
from dotenv import load_dotenv

load_dotenv()

dashboard_blueprint = Blueprint('dashboard', __name__, template_folder="../templates")


STEAM_API_KEY = os.getenv("STEAM_API_KEY")

def get_steam_user_info(steam_id):
    """Obtém as informações do usuário pela API da Steam."""
    url = f"https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/"
    params = {"key": STEAM_API_KEY, "steamids": steam_id}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        players = data.get("response", {}).get("players", [])
        if players:
            return players[0]  # Retorna o primeiro (e único) jogador encontrado
    return None


@dashboard_blueprint.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    """Página do usuário após login."""
    if "steam_id" not in session:
        return redirect(url_for("home"))

    user_steam_id = session["steam_id"]

    # Obter informações do usuário
    user_info = get_steam_user_info(user_steam_id)
    if not user_info:
        return redirect(url_for("logout"))

    form = TradeLinkForm()  # Instancie o formulário

    tradelink = None
    inventory = []

    if form.validate_on_submit():  # Verifica se o formulário foi submetido corretamente
        tradelink = form.tradelink.data

        # Buscar inventário do usuário
        result = fetch_inventory(tradelink, user_steam_id)
        if "error" in result:
            return render_template(
                "dashboard.html",
                form=form,
                error=result["error"],
                inventory=[],
                tradelink=tradelink,
                user_info=user_info,  # Passa as informações do usuário
            )

        inventory = result.get("inventory", [])
        return render_template(
            "dashboard.html",
            form=form,
            inventory=inventory,
            tradelink=tradelink,
            error=None if inventory else "Seu inventário está vazio.",
            user_info=user_info,  # Passa as informações do usuário
        )

    return render_template(
        "dashboard.html",
        form=form,
        inventory=inventory,
        tradelink=tradelink,
        error=None,
        user_info=user_info,  # Passa as informações do usuário
    )


@dashboard_blueprint.route("/logout")
def logout():
    """Realiza logout e limpa a sessão."""
    session.clear()  # Limpa todos os dados da sessão
    return redirect(url_for("home.home"))  # Redireciona para a página inicial
