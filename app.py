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
#from flask_wtf.csrf import CSRFProtect


# Carregar variáveis de ambiente
load_dotenv()


app = Flask(__name__)



#csrf = CSRFProtect(app)
app.secret_key = os.getenv("SECRET_KEY")

BOT_USERNAME = os.getenv("BOT_USERNAME")
BOT_PASSWORD = os.getenv("BOT_PASSWORD")
TRADE_URL = os.getenv("TRADE_URL")
STEAM_API_KEY = os.getenv("STEAM_API_KEY")
#STEAM_GUARD= os.getenv("STEAM_GUARD")

SHARED_SECRET= os.getenv("SHARED_SECRET")
IDENTITY_SECRET= os.getenv("IDENTITY_SECRET")


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
        print("Iniciando o endpoint '/enviar-oferta'")

        # Recebe os dados do frontend
        dados = request.json
        print(f"Dados recebidos do frontend: {dados}")
        
        itens_selecionados = dados.get("itens")  # Ex.: [{'assetid': '12345', 'appid': '730'}]
        tradelink = dados.get("tradelink")  # Link de troca do usuário

        # Validação básica
        if not itens_selecionados:
            print("Nenhum item foi selecionado pelo usuário.")
            return jsonify({"erro": "Nenhum item foi selecionado"}), 400

        if not tradelink or "https://steamcommunity.com/tradeoffer/new/?" not in tradelink:
            print(f"Tradelink inválido recebido: {tradelink}")
            return jsonify({"erro": "Tradelink inválido"}), 400

        # Caminho para o arquivo SteamGuard
        steam_guard_file = r"C:\Users\Tito el mestre\Documents\GitHub\documentacaoFlask---Copia\SteamGuard.txt"


        # Login no bot
        print("Tentando realizar login no bot...")
        steam_client.login(username=BOT_USERNAME, password=BOT_PASSWORD, steam_guard=steam_guard_file)
        print("Login no bot realizado com sucesso.")

        if steam_client.is_session_alive():
             print("Sessão ativa, pronto para realizar ações.")
        else:
            print("Falha na autenticação. A sessão não está ativa.")

        # Monta a oferta de troca
        itens_para_receber = [
            {"assetid": item['assetid'], "appid": item['appid'], "contextid": "2"}
            for item in itens_selecionados
        ]
        print(f"Itens para receber (do usuário): {itens_para_receber}")

        # Envia a oferta para o usuário
        print(f"Enviando oferta para o tradelink do usuário: {tradelink}")
        steam_client.make_offer_with_url(
            items_from_me=[],  # Nenhum item do lado do bot
            items_from_them=itens_para_receber,  # Itens que o usuário está oferecendo
            trade_offer_url=tradelink,  # Tradelink do usuário
            message="Obrigado por vender seus itens para o nosso site!"
        )
        print("Oferta enviada com sucesso.")

        return jsonify({"mensagem": "Oferta enviada com sucesso!"}), 200

    except Exception as e:
        print(f"Erro ao enviar a oferta: {e}")
        return jsonify({"erro": f"Erro ao enviar a oferta: {str(e)}"}), 500

    finally:
        try:
            print("Tentando realizar logout do bot...")
            steam_client.logout()
            print("Logout realizado com sucesso.")
        except Exception as logout_error:
            print(f"Erro ao realizar logout: {logout_error}")






if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)