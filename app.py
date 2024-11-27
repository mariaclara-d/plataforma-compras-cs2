from flask import Flask, session, redirect, request, url_for, jsonify
from dotenv import load_dotenv
import os
import requests
from auth import steam_login
from inventory import fetch_inventory
from inventory import validate_tradelink
from flask import render_template
from steampy.client import SteamClient
from steampy.exceptions import InvalidCredentials


# Carregar variáveis de ambiente
load_dotenv()


app = Flask(__name__)


app.secret_key = os.getenv("SECRET_KEY")

BOT_USERNAME = os.getenv("BOT_USERNAME")
BOT_PASSWORD = os.getenv("BOT_PASSWORD")
TRADE_URL = os.getenv("TRADE_URL")
STEAM_API_KEY = os.getenv("STEAM_API_KEY")
STEAM_GUARD_FILE= os.getenv("STEAM_GUARD_FILE")

STEAM_OPENID_URL = "https://steamcommunity.com/openid/login"

# Inicializar o cliente do bot
steam_client = SteamClient(STEAM_API_KEY)


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



@app.route('/enviar-oferta', methods=['POST'])
def enviar_oferta():
    try:
        # Recebe os dados do frontend (itens selecionados pelo usuário e tradelink)
        dados = request.json
        itens_selecionados = dados.get("itens")  # Ex.: [{'assetid': '12345', 'appid': '730'}]
        tradelink = dados.get("tradelink")  # Link de troca do usuário

        # Validação básica
        if not itens_selecionados:
            return jsonify({"erro": "Nenhum item foi selecionado"}), 400
        if not tradelink or "https://steamcommunity.com/tradeoffer/new/?" not in tradelink:
            return jsonify({"erro": "Tradelink inválido"}), 400

        # Login no bot
        steam_client.login(BOT_USERNAME, BOT_PASSWORD, STEAM_GUARD_FILE)

        # Monta a oferta de troca
        itens_para_enviar = [
            {"assetid": item['assetid'], "appid": item['appid'], "contextid": "2"}
            for item in itens_selecionados
        ]

        # Envia a oferta para o dono do site
        steam_client.make_offer_with_url(
            items_from_me=itens_para_enviar,
            items_from_them=[],  # Nenhum item do lado do dono
            trade_offer_url=TRADE_URL,  # Tradelink do dono
            message="Oferta gerada pelo site."
        )

        return jsonify({"mensagem": "Oferta enviada com sucesso!"}), 200

    except Exception as e:
        return jsonify({"erro": f"Erro ao enviar a oferta: {str(e)}"}), 500

    finally:
        try:
            steam_client.logout()
        except:
            pass




if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
