from flask import Blueprint, session, redirect, url_for, render_template, request
from services.inventory_service import InventoryService
from utils.auth_helpers import require_auth
from middleware.rate_limiting import rate_limit
import logging

inventory_blueprint = Blueprint('inventory', __name__, template_folder="../templates")
inventory_service = InventoryService()

@inventory_blueprint.route("/inventory", methods=["GET", "POST"])
@require_auth
@rate_limit(max_requests=30, window_seconds=60)  # 30 requests per minute
def inventory():
    user_steam_id = session["steam_id"]

    if request.method == "POST":
        tradelink = request.form.get("tradelink")
        
        # Rate limiting adicional para operações POST
        if not rate_limit(max_requests=10, window_seconds=300)():
            return render_template(
                "inventory.html",
                inventory=None,
                tradelink=None,
                error="Muitas tentativas. Aguarde alguns minutos."
            )
        
        result = inventory_service.fetch_inventory(tradelink, user_steam_id)
        
        if isinstance(result, tuple) and result[1] == 400:
            return render_template(
                "inventory.html",
                inventory=None,
                tradelink=None,
                error=result[0]["error"]
            )

        if "inventory" in result and result["inventory"]:
            logging.info(f"[INVENTORY_PAGE] Inventário carregado com {len(result['inventory'])} itens")
            return render_template(
                "inventory.html",
                inventory=result["inventory"],
                tradelink=tradelink,
                error=None
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
