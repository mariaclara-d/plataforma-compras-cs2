from flask import Blueprint, session, redirect, url_for, render_template, jsonify, request
import os
import requests
from dotenv import load_dotenv
import logging

# Carregar variáveis de ambiente
load_dotenv()

inventory_blueprint = Blueprint('inventory', __name__, template_folder="../templates")

# Inicializar a chave da API Steam
steam_api_key_inventory = os.getenv("STEAM_API_KEY_NAO_OFICIAL")

# Função para validar se o tradelink corresponde ao usuário logado
def validate_tradelink(tradelink, user_steam_id):
    try:
        tradelink_steam_id = tradelink.split("partner=")[1].split("&")[0]
        partner_id = int(tradelink_steam_id)
        calculated_steam_id = str(partner_id + 76561197960265728)
    except (IndexError, ValueError):
        logging.warning("Tradelink está no formato incorreto.")
        return False

    user_steam_id = user_steam_id.replace("https://steamcommunity.com/openid/id/", "")

    if calculated_steam_id != user_steam_id:
        logging.warning(f"Tradelink ID ({calculated_steam_id}) não corresponde ao user_steam_id ({user_steam_id}).")
        return False

    logging.info("Tradelink validado com sucesso!")
    return True

# Função para obter o inventário do usuário usando a API da Steam
def get_user_inventory(steam_api_key_inventory, user_steam_id):
    if user_steam_id.startswith("https://steamcommunity.com/openid/id/"):
        user_steam_id = user_steam_id.replace("https://steamcommunity.com/openid/id/", "")

    url = f"https://www.steamwebapi.com/steam/api/inventory?key={steam_api_key_inventory}&steam_id={user_steam_id}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        inventory = []
        for item in data:
            inventory_item = {
                "name": item.get("marketname", "N/A"),
                "assetid": item.get("assetid"),
                "tradable": item.get("tradable", False),
                "image_url": item.get("image", ""),
                "rarity": item.get("rarity", "N/A"),
                "quality": item.get("quality", "N/A"),
                "price_median": item.get("pricemedian"),
                "price_safe": item.get("pricesafe"),
                "price_avg": item.get("priceavg"),
                "price_min": item.get("pricemin"),
                "price_max": item.get("pricemax"),
                "inspect_link": item.get("inspectlink", "")
            }
            inventory.append(inventory_item)
        return inventory
    except (requests.RequestException, ValueError) as e:
        logging.error(f"Erro ao buscar/processar inventário para o ID {user_steam_id}: {str(e)}")
        return []

# Função principal para retornar o inventário validado
def fetch_inventory(tradelink, user_steam_id):
    if not validate_tradelink(tradelink, user_steam_id):
        return {"error": "Tradelink não corresponde ao usuário logado."}, 400

    inventory = get_user_inventory(steam_api_key_inventory, user_steam_id)
    return {
        "steam_id": user_steam_id,
        "tradelink": tradelink,
        "inventory": inventory
    }

@inventory_blueprint.route("/inventory", methods=["GET", "POST"])
def inventory():
    if "steam_id" not in session:
        return redirect(url_for("auth.steam_login"))

    user_steam_id = session["steam_id"]

    if request.method == "POST":
        tradelink = request.form.get("tradelink")

        if not validate_tradelink(tradelink, user_steam_id):
            return render_template(
                "inventory.html",
                inventory=None,
                tradelink=None,
                error="Tradelink inválido. Por favor, insira novamente."
            )

        inventory_data = fetch_inventory(tradelink, user_steam_id)

        if "inventory" in inventory_data:
            return render_template(
                "inventory.html",
                inventory=inventory_data["inventory"],
                tradelink=tradelink
            )

        return render_template(
            "inventory.html",
            inventory=None,
            tradelink=tradelink,
            error="Erro ao buscar inventário ou inventário vazio."
        )

    return render_template(
        "inventory.html",
        inventory=None,
        tradelink=None,
        error=None
    )
