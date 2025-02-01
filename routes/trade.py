from flask import Blueprint, request, jsonify
from steampy.client import SteamClient, Asset, GameOptions  # Asset pode ser útil para manipulação de itens
import os
import re
from dotenv import load_dotenv
from models import TradeOffer
from datetime import datetime, timedelta
from db_config import db

load_dotenv()
trade_blueprint = Blueprint('trade', __name__, template_folder="../templates")
STEAM_API_KEY = os.getenv("STEAM_API_KEY")
game_options = GameOptions(app_id=730, context_id=2)

def extrair_partner_steamid(tradelink):
    match = re.search(r"partner=(\d+)", tradelink)
    return match.group(1) if match else None

def steamid32_to_steamid64(steamid32):
    try:
        return int(steamid32) + 76561197960265728
    except ValueError:
        raise ValueError("SteamID32 inválido")


@trade_blueprint.route('/enviar-oferta', methods=['POST'])
def enviar_oferta_com_steampy():
    try:
        print("Iniciando o endpoint '/enviar-oferta' com Steampy")
        dados = request.json
        if not dados:
            return jsonify({"erro": "Dados ausentes na requisição"}), 400

        itens_selecionados = dados.get("itens")
        tradelink = dados.get("tradelink")

        if not itens_selecionados or not isinstance(itens_selecionados, list):
            return jsonify({"erro": "Nenhum item válido foi selecionado"}), 400

        for item in itens_selecionados:
            if not isinstance(item, dict) or "assetid" not in item:
                return jsonify({"erro": "Um ou mais itens possuem formato inválido"}), 400

        if not tradelink or "https://steamcommunity.com/tradeoffer/new/?" not in tradelink:
            return jsonify({"erro": "Tradelink inválido"}), 400

        partner_steamid32 = extrair_partner_steamid(tradelink)
        if not partner_steamid32:
            return jsonify({"erro": "Tradelink inválido"}), 400

        try:
            partner_steamid64 = steamid32_to_steamid64(partner_steamid32)
        except ValueError:
            return jsonify({"erro": "SteamID inválido"}), 400

        steam_client = SteamClient(STEAM_API_KEY)
        steam_guard_path = './steam_guard.json'

        if not os.path.exists(steam_guard_path):
            return jsonify({"erro": "Arquivo steam_guard.json não encontrado"}), 500

        try:
            steam_client.login(
                username=os.getenv("STEAM_USERNAME"),
                password=os.getenv("STEAM_PASSWORD"),
                steam_guard=steam_guard_path
            )
            print("Login realizado com sucesso!")
        except Exception as e:
            print(f"Erro no login: {e}")
            return jsonify({"erro": "Falha ao realizar login no Steam"}), 500

        if steam_client.is_session_alive():
            print("Sessão ativa")
        else:
            print("Sessão inativa")           

        # Converter os itens para o formato esperado (dicionários)
        formatted_items = [
            Asset(asset_id=item["assetid"], game=game_options)
            for item in itens_selecionados
        ]

        print("Itens selecionados:", itens_selecionados)
        print("Itens formatados como dicionários:", formatted_items)
        print("Itens a serem enviados:")
        print(f"items_from_me: [] (vazio, o site apenas recebe)")
        print(f"items_from_them: {formatted_items}")
        print(f"Tradelink: {tradelink}")

        try:
            offer = steam_client.make_offer_with_url(
                items_from_me=[],  # O site não envia itens
                items_from_them=formatted_items,  # Itens formatados como dicionários
                trade_offer_url=tradelink,
                message="Obrigado por vender seus itens para o nosso site!"
            )

            # Verifique se a oferta foi criada com sucesso
            if offer is None:
                print("Erro: A oferta não foi criada corretamente.")
                return jsonify({"erro": "Erro ao criar a oferta: retorno None"}), 500

            print("Retorno da oferta:", offer)
            if isinstance(offer, dict) and 'tradeofferid' in offer:
                offer_id = offer['tradeofferid']

                # Insere a oferta no banco de dados
                nova_oferta = TradeOffer(
                    tradeofferid=offer_id,
                    partnersteamid=partner_steamid64,
                    status='pendente',  # Status inicial
                    expires_at=datetime.now() + timedelta(minutes=10)  # Expira em 10 minutos
                )
                db.session.add(nova_oferta)
                db.session.commit()

                return jsonify({
                    "mensagem": "Oferta criada com sucesso!",
                    "offer_id": offer_id
                }), 200
            else:
                print(f"Retorno inesperado: {offer}")
                return jsonify({"erro": "Erro no retorno do Steampy"}), 500

        except Exception as e:
            print(f"Erro ao criar oferta: {e}")
            return jsonify({"erro": f"Erro ao criar oferta: {str(e)}"}), 500

    except Exception as e:
        print(f"Erro interno: {e}")
        return jsonify({"erro": f"Erro interno: {str(e)}"}), 500