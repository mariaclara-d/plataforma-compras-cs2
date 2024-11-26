from flask import Flask, session, redirect, request, url_for, jsonify
from dotenv import load_dotenv
import os
import requests
from auth import steam_login
from inventory import fetch_inventory
from inventory import validate_tradelink
from flask import render_template

# Carregar variáveis de ambiente
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
print("Chave secreta:", app.secret_key)

STEAM_OPENID_URL = "https://steamcommunity.com/openid/login"

def verify_steam_response(args):
    """Verifica a resposta do OpenID da Steam."""
    params = {
        "openid.assoc_handle": args.get("openid.assoc_handle"),
        "openid.sig": args.get("openid.sig"),
        "openid.signed": args.get("openid.signed"),
        "openid.ns": args.get("openid.ns"),
        "openid.mode": "check_authentication",
        **{key: args[key] for key in args.get("openid.signed").split(",")}
    }
    response = requests.post(STEAM_OPENID_URL, data=params)
    print("Parâmetros enviados para validação:", params)
    print("Resposta Steam OpenID:", response.text)
    return "is_valid:true" in response.text


@app.route("/")
def home():
    """Página inicial."""
    print("Sessão atual:", session)
    if "steam_id" in session:
        return f"""
            <h1>Bem-vindo, Steam ID: {session['steam_id']}!</h1>
            <a href='/inventory'>Ver inventário</a>
        """
    return """
        <h1>Bem-vindo ao site de compras de skins!</h1>
        <p><a href="/login">Clique aqui para entrar com Steam</a></p>
    """

@app.route("/login")
def login():
    steam_openid_url = (
        "https://steamcommunity.com/openid/login?"
        "openid.ns=http://specs.openid.net/auth/2.0&"
        "openid.mode=checkid_setup&"
        "openid.identity=http://specs.openid.net/auth/2.0/identifier_select&"
        "openid.claimed_id=http://specs.openid.net/auth/2.0/identifier_select&"
        f"openid.return_to={request.host_url}complete_steam_login&"
        f"openid.realm={request.host_url}"
    )
    return redirect(steam_openid_url)

@app.route("/complete_steam_login")
def complete_steam_login():
    steam_id = request.args.get('openid.claimed_id')
    if steam_id:
        session["steam_id"] = steam_id  # Salva o ID da Steam na sessão
        return redirect(url_for('home'))  # Redireciona para a página principal
    return 'Erro na autenticação da Steam', 400
    

from steampy.client import SteamClient

@app.route("/inventory", methods=["GET", "POST"])
def inventory():
    """Exibe o inventário do usuário e permite selecionar itens para troca."""
    if "steam_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        tradelink = request.form.get("tradelink")
        user_steam_id = session.get("steam_id")

        # Validar tradelink
        if not validate_tradelink(tradelink, user_steam_id):
            return "<p>Tradelink inválido. Por favor, insira novamente.</p>"

        # Buscar inventário
        inventory_data = fetch_inventory(tradelink, user_steam_id)

        # Se o inventário for válido, renderizar a página com os itens
        if "inventory" in inventory_data:
            return render_template(
                "inventory.html", 
                inventory=inventory_data["inventory"], 
                tradelink=tradelink
            )
        else:
            return "<p>Erro ao buscar inventário ou inventário vazio.</p>"

    # Página inicial de inserção do tradelink
    return render_template("tradelink.html")


@app.route("/send_offer", methods=["POST"])
def send_offer():
    """Recebe os itens selecionados e envia uma oferta de troca para o dono do site."""
    if "steam_id" not in session:
        return redirect(url_for("login"))

    tradelink = request.form.get("tradelink")
    item_ids = request.form.getlist("item_ids")
    user_steam_id = session.get("steam_id")

    # Validar o tradelink
    if not validate_tradelink(tradelink, user_steam_id):
        return "<p>Erro: O tradelink fornecido não corresponde à sua conta Steam.</p>"

    if not item_ids:
        return "<p>Nenhum item selecionado.</p>"

    # Configurar informações do bot (dono do site)
    steam_api_key = os.getenv("BOT_API_KEY")
    bot_username = os.getenv("BOT_USERNAME")
    bot_password = os.getenv("BOT_PASSWORD")
  

    # Inicializar cliente Steam
    steam_client = SteamClient(steam_api_key)

    try:
        # Login no bot
        steam_client.login(bot_username, bot_password)

        # Criar e enviar a oferta de troca
        offer = steam_client.make_offer_with_url(items_from_me=[], items_from_them=item_ids, trade_offer_url=tradelink)
        response = offer.send()

        if "tradeofferid" in response:
            return f"<p>Oferta enviada com sucesso! ID da oferta: {response['tradeofferid']}</p>"
        else:
            return "<p>Erro ao enviar oferta. Verifique o tradelink e tente novamente.</p>"

    except Exception as e:
        print(f"Erro ao enviar oferta: {e}")
        return "<p>Erro ao enviar oferta. Tente novamente mais tarde.</p>"

    finally:
        # Logout do bot após enviar a oferta
        steam_client.logout()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
