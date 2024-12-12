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
# from flask_wtf.csrf import CSRFProtect
from steampy.client import SteamClient, Asset
from steampy.utils import GameOptions
import json
import re 


# Carregar variáveis de ambiente
load_dotenv()


app = Flask(__name__)


# csrf = CSRFProtect(app)
app.secret_key = os.getenv("SECRET_KEY")

BOT_USERNAME = os.getenv("BOT_USERNAME")
BOT_PASSWORD = os.getenv("BOT_PASSWORD")
TRADE_URL = os.getenv("TRADE_URL")
STEAM_API_KEY = os.getenv("STEAM_API_KEY")
#STEAM_GUARD_FILE= os.getenv("STEAM_GUARD_FILE")


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


def extrair_partner_steamid(tradelink):
    """
    Extrai o SteamID64 do parceiro a partir do tradelink.
    """
    # Padrão para capturar o parceiro no tradelink
    match = re.search(r"partner=(\d+)", tradelink)
    return match.group(1) if match else None

def steamid32_to_steamid64(steamid32):
    try:
        return int(steamid32) + 76561197960265728
    except ValueError:
        raise ValueError("SteamID32 inválido")

@app.route('/enviar-oferta', methods=['POST'])
def enviar_oferta():
    try:
        print("Iniciando o endpoint '/enviar-oferta'")

        # Recebe os dados do frontend
        dados = request.json
        if not dados:
            print("Nenhum dado foi enviado no corpo da requisição.")
            return jsonify({"erro": "Dados ausentes na requisição"}), 400

        itens_selecionados = dados.get("itens")
        tradelink = dados.get("tradelink")

        # Validação dos dados recebidos
        if not itens_selecionados or not isinstance(itens_selecionados, list):
            print("Nenhum item válido foi selecionado pelo usuário.")
            return jsonify({"erro": "Nenhum item válido foi selecionado"}), 400

        for item in itens_selecionados:
            if not isinstance(item, dict) or "assetid" not in item:
                print(f"Item inválido encontrado: {item}")
                return jsonify({"erro": "Um ou mais itens possuem formato inválido"}), 400

        if not tradelink or "https://steamcommunity.com/tradeoffer/new/?" not in tradelink:
            print(f"Tradelink inválido recebido: {tradelink}")
            return jsonify({"erro": "Tradelink inválido"}), 400

        # Extrair o SteamID32 do tradelink
        match = re.search(r"partner=(\d+)", tradelink)
        if not match:
            print(f"Não foi possível extrair o SteamID32 do tradelink: {tradelink}")
            return jsonify({"erro": "Tradelink inválido"}), 400

        partner_steamid32 = match.group(1)

        # Converter SteamID32 para SteamID64
        try:
            partner_steamid64 = steamid32_to_steamid64(partner_steamid32)
        except ValueError as e:
            print(f"Erro ao converter SteamID32: {e}")
            return jsonify({"erro": "SteamID inválido"}), 400

        # Dados para a API
        payload = {
            "steamloginsecure": os.getenv("STEAM_LOGIN_SECURE"),
            "partneritemassetids": ",".join(item["assetid"] for item in itens_selecionados),
            "tradelink": tradelink,
            "partnersteamid": str(partner_steamid64),
            "message": "Obrigado por vender seus itens para o nosso site!",
        }

        print("Enviando requisição para a API de trocas...")
        try:
            response = requests.post(
                f"https://www.steamwebapi.com/steam/api/trade/create?key={os.getenv('STEAM_API_KEY_NAO_OFICIAL')}",
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            print("Oferta criada com sucesso!")
            return jsonify({"mensagem": "Oferta criada com sucesso!"}), 200
        except requests.exceptions.RequestException as e:
            print(f"Erro ao conectar à API: {e}")
            return jsonify({"erro": "Falha na comunicação com a API"}), 500

    except Exception as e:
        print(f"Erro inesperado: {e}")
        import traceback
        print(traceback.format_exc())
        return jsonify({"erro": "Ocorreu um erro inesperado no servidor"}), 500



if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
    


