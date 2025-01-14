import os
import re
import requests
from flask import Blueprint, request, jsonify

# Blueprint para rotas relacionadas a trades
trade_blueprint = Blueprint('trade', __name__)

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

@trade_blueprint.route('/enviar-oferta', methods=['POST'])
def enviar_oferta():
    try:
        print("Iniciando o endpoint '/enviar-oferta'")
        dados = request.json
        if not dados:
            print("Nenhum dado foi enviado no corpo da requisição.")
            return jsonify({"erro": "Dados ausentes na requisição"}), 400

        itens_selecionados = dados.get("itens")
        tradelink = dados.get("tradelink")

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

        match = re.search(r"partner=(\d+)", tradelink)
        if not match:
            print(f"Não foi possível extrair o SteamID32 do tradelink: {tradelink}")
            return jsonify({"erro": "Tradelink inválido"}), 400

        partner_steamid32 = match.group(1)

        try:
            partner_steamid64 = steamid32_to_steamid64(partner_steamid32)
        except ValueError as e:
            print(f"Erro ao converter SteamID32: {e}")
            return jsonify({"erro": "SteamID inválido"}), 400

        payload = {
            "steamloginsecure": os.getenv("STEAM_LOGIN_SECURE"),
            "partneritemassetids": ",".join(item["assetid"] for item in itens_selecionados),
            "myitemassetids": "",  # Se necessário, adicionar IDs de itens próprios
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
