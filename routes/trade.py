# routes/trade.py

from flask import Blueprint, request, jsonify
import asyncio
from services.aiosteampy_service import (
    realizar_login_aiosteampy,
    enviar_oferta_aiosteampy,
    registrar_oferta_no_banco,
    validar_dados_requisicao,
)

trade_blueprint = Blueprint('trade', __name__, template_folder="../templates")

@trade_blueprint.route('/enviar-oferta', methods=['POST'])
def enviar_oferta_com_aiosteampy():
    print("📨 Iniciando o endpoint '/enviar-oferta' com aiosteampy")
    dados = request.json

    if not dados:
        return jsonify({"erro": "Dados ausentes na requisição"}), 400

    try:
        itens_selecionados, tradelink, partner_steamid64 = validar_dados_requisicao(dados)
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400

    try:
        # Executa tudo dentro de um único loop assíncrono
        async def fluxo_envio():
            client = await realizar_login_aiosteampy()
            offer_id = await enviar_oferta_aiosteampy(
                client,
                tradelink,
                [item["assetid"] for item in itens_selecionados]
            )
            await registrar_oferta_no_banco(offer_id, partner_steamid64)
            return offer_id

        offer_id = asyncio.run(fluxo_envio())

    except Exception as e:
        print(f"Erro interno: {e}")
        return jsonify({"erro": f"Erro interno: {str(e)}"}), 500

    return jsonify({
        "mensagem": "Oferta criada com sucesso!",
        "offer_id": offer_id
    }), 200

