import os
import re
import requests
import jwt
from dotenv import load_dotenv
from flask import Blueprint, request, jsonify

# Blueprint para rotas relacionadas a trades
trade_blueprint = Blueprint('trade', __name__)

# Carregar variáveis de ambiente
load_dotenv()

STEAM_API_KEY_NAO_OFICIAL = os.getenv("STEAM_API_KEY_NAO_OFICIAL")
STEAM_LOGIN_SECURE = os.getenv("STEAM_LOGIN_SECURE")


def verificar_expiracao(cookie):
    try:
        # Decodificar o cookie para verificar a validade
        payload = jwt.decode(cookie, options={"verify_signature": False})
        exp = payload.get("exp")
        if exp:
            from datetime import datetime
            tempo_restante = exp - int(datetime.now().timestamp())
            if tempo_restante < 86400:  # Menos de 1 dia
                print("Aviso: STEAM_LOGIN_SECURE está próximo de expirar.")
    except Exception as e:
        print(f"Erro ao verificar expiração do cookie: {e}")
        

def extrair_partner_steamid(tradelink):
    """
    Extrai o SteamID64 do parceiro a partir do tradelink.
    """
    match = re.search(r"partner=(\d+)", tradelink)
    return match.group(1) if match else None

def steamid32_to_steamid64(steamid32):
    try:
        return int(steamid32) + 76561197960265728
    except ValueError:
        raise ValueError("SteamID32 inválido")

def validar_assetids(itens, inventario):
    """
    Valida se os AssetIDs dos itens existem no inventário.
    """
    assetids_validos = {item["assetid"] for item in inventario}
    for item in itens:
        if item["assetid"] not in assetids_validos:
            print(f"AssetID inválido ou não encontrado no inventário: {item['assetid']}")
            return False
    return True

@trade_blueprint.route('/enviar-oferta', methods=['POST'])
def enviar_oferta():
    try:
        print("Iniciando o endpoint '/enviar-oferta'")
        
        # Obter dados do corpo da requisição
        dados = request.json
        if not dados:
            print("Nenhum dado foi enviado no corpo da requisição.")
            return jsonify({"erro": "Dados ausentes na requisição"}), 400

        itens_selecionados = dados.get("itens")
        tradelink = dados.get("tradelink")

        # Validação básica dos dados enviados
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

        # Extrair partner SteamID
        partner_steamid32 = extrair_partner_steamid(tradelink)
        if not partner_steamid32:
            print(f"Não foi possível extrair o SteamID32 do tradelink: {tradelink}")
            return jsonify({"erro": "Tradelink inválido"}), 400

        try:
            partner_steamid64 = steamid32_to_steamid64(partner_steamid32)
        except ValueError as e:
            print(f"Erro ao converter SteamID32: {e}")
            return jsonify({"erro": "SteamID inválido"}), 400

        # Verificar STEAM_LOGIN_SECURE
        if not STEAM_LOGIN_SECURE:
            print("STEAM_LOGIN_SECURE não configurado corretamente.")
            return jsonify({"erro": "Configuração do servidor inválida"}), 500

        # Montar payload
        payload = {
            "steamloginsecure": STEAM_LOGIN_SECURE,
            "partneritemassetids": ",".join(item["assetid"] for item in itens_selecionados),
            "myitemassetids": "",
            "tradelink": tradelink,
            "partnersteamid": str(partner_steamid64),
            "message": "Obrigado por vender seus itens para o nosso site!",
        }

        print("Enviando requisição para a API de trocas...")
        print(f"Payload: {payload}")

        try:
            # Chamada para a API da Steam
            response = requests.post(
                f"https://www.steamwebapi.com/steam/api/trade/create?key={STEAM_API_KEY_NAO_OFICIAL}",
                json=payload,
                timeout=10
            )
            print(f"Resposta da API: {response.status_code} - {response.text}")
            
            # Analisar erros específicos retornados pela API
            if response.status_code == 406:
                print("Erro 406: ID de ativo inválido ou muitas ofertas comerciais pendentes.")
                return jsonify({"erro": "Um ou mais itens selecionados são inválidos ou existem muitas ofertas pendentes."}), 406

            response.raise_for_status()  # Levanta exceções para erros HTTP

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

