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

# Carregar variáveis de ambiente
load_dotenv()


app = Flask(__name__)


# csrf = CSRFProtect(app)
app.secret_key = os.getenv("SECRET_KEY")

BOT_USERNAME = os.getenv("BOT_USERNAME")
BOT_PASSWORD = os.getenv("BOT_PASSWORD")
TRADE_URL = os.getenv("TRADE_URL")
STEAM_API_KEY = os.getenv("STEAM_API_KEY")
# STEAM_GUARD_FILE= os.getenv("STEAM_GUARD_FILE")


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


def carregar_cookies():
    try:
        # Carrega os cookies do arquivo cookies.json
        if os.path.exists('cookies.json'):
            with open('cookies.json', 'r') as f:
                cookies = json.load(f)
                steam_client.set_login_cookies(cookies)
                print("Cookies carregados e sessão configurada.")
        else:
            print("Arquivo cookies.json não encontrado.")
    except Exception as e:
        print(f"Erro ao carregar cookies: {e}")


@app.route('/enviar-oferta', methods=['POST'])
def enviar_oferta():
    try:
        print("Iniciando o endpoint '/enviar-oferta'")

        # Recebe os dados do frontend
        dados = request.json
        print(f"Dados recebidos do frontend: {dados}")

        # Obtém os itens e o tradelink do frontend
        itens_selecionados = dados.get("itens")
        tradelink = dados.get("tradelink")

        # Validação dos dados recebidos
        if not itens_selecionados or not isinstance(itens_selecionados, list):
            print("Nenhum item válido foi selecionado pelo usuário.")
            return jsonify({"erro": "Nenhum item válido foi selecionado"}), 400

        if not tradelink or "https://steamcommunity.com/tradeoffer/new/?" not in tradelink:
            print(f"Tradelink inválido recebido: {tradelink}")
            return jsonify({"erro": "Tradelink inválido"}), 400

        # Caminho do arquivo SteamGuard.json
        steam_guard_file = os.getenv("STEAM_GUARD_FILE", "SteamGuard.json")

        if not os.path.exists(steam_guard_file):
            print(f"Arquivo SteamGuard não encontrado em {steam_guard_file}")
            return jsonify({"erro": "Arquivo SteamGuard não encontrado"}), 500

        # Login no bot
        try:
            # Carrega cookies
            carregar_cookies()

            # Carrega o arquivo SteamGuard
            with open(steam_guard_file, 'r') as f:
                steam_guard_data = json.load(f)

            # Obtém as credenciais do SteamGuard
            BOT_USERNAME = steam_guard_data.get('username')
            BOT_PASSWORD = steam_guard_data.get('password')

            print("Tentando realizar login no bot...")

            # Realiza login se a sessão não está ativa
            if not steam_client.is_session_alive():
                steam_client.login(BOT_USERNAME, BOT_PASSWORD, steam_guard_file)
                print("Login no bot realizado com sucesso.")

                # Salva cookies após o login inicial
                cookies = steam_client.get_cookies()
                with open('cookies.json', 'w') as f:
                    json.dump(cookies, f)
                print("Cookies salvos com sucesso.")

        except InvalidCredentials:
            return jsonify({"erro": "Credenciais inválidas para o bot"}), 401
        except Exception as login_error:
            return jsonify({"erro": f"Erro ao fazer login: {login_error}"}), 500

        # Verificar se a sessão está ativa
        if not steam_client.is_session_alive():
            print("Sessão do bot não está ativa.")
            return jsonify({"erro": "Sessão do bot não está ativa"}), 500

        # Monta e envia a oferta de troca
        try:
            game = GameOptions.CS  # Define o jogo CS:GO
            itens_para_receber = [
                Asset(item['assetid'], game) for item in itens_selecionados
            ]

            print(f"Itens para receber: {itens_para_receber}")

            # Envia a oferta ao tradelink do usuário
            print(f"Enviando oferta para o tradelink: {tradelink}")
            steam_client.make_offer_with_url(
                items_from_me=[],  # Nenhum item do lado do bot
                items_from_them=itens_para_receber,
                trade_offer_url=tradelink,
                message="Obrigado por vender seus itens para o nosso site!"
            )

            print("Oferta enviada com sucesso.")
            return jsonify({"mensagem": "Oferta enviada com sucesso!"}), 200

        except Exception as offer_error:
            print(f"Erro ao enviar a oferta: {offer_error}")
            return jsonify({"erro": f"Erro ao enviar oferta: {offer_error}"}), 500

    finally:
        try:
            # Tenta fazer logout corretamente
            if steam_client.is_session_alive():
                print("Tentando realizar logout do bot...")
                steam_client.logout()
                print("Logout realizado com sucesso.")
            else:
                print("Nenhuma sessão ativa para realizar logout.")

        except Exception as logout_error:
            print(f"Erro ao realizar logout: {logout_error}")

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)