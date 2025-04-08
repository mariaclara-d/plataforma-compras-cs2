from flask import Blueprint, request, jsonify
from services.steam_service import (
    validar_dados_requisicao,
    realizar_login_steam,
    formatar_itens_recebidos,
    criar_oferta,
    registrar_oferta_no_banco
)

trade_blueprint = Blueprint('trade', __name__, template_folder="../templates")

@trade_blueprint.route('/enviar-oferta', methods=['POST'])
def enviar_oferta_com_steampy():
    try:
        print("Iniciando o endpoint '/enviar-oferta' com Steampy")
        dados = request.json

        if not dados:
            return jsonify({"erro": "Dados ausentes na requisição"}), 400

        try:
            itens_selecionados, tradelink, partner_steamid64 = validar_dados_requisicao(dados)
        except ValueError as e:
            return jsonify({"erro": str(e)}), 400

        try:
            steam_client = realizar_login_steam()
        except Exception as e:
            return jsonify({"erro": f"Falha no login Steam: {str(e)}"}), 500

        itens_formatados = formatar_itens_recebidos(itens_selecionados)

        try:
            offer = criar_oferta(steam_client, itens_formatados, tradelink)
        except Exception as e:
            return jsonify({"erro": f"Erro ao criar oferta: {str(e)}"}), 500

        if offer and isinstance(offer, dict) and 'tradeofferid' in offer:
            registrar_oferta_no_banco(offer['tradeofferid'], partner_steamid64)
            return jsonify({
                "mensagem": "Oferta criada com sucesso!",
                "offer_id": offer['tradeofferid']
            }), 200
        else:
            return jsonify({"erro": "Erro no retorno do Steampy"}), 500

    except Exception as e:
        print(f"Erro interno: {e}")
        return jsonify({"erro": f"Erro interno: {str(e)}"}), 500




