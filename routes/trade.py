from flask import Blueprint, request, jsonify
from services.aiosteampy_service import (
    realizar_login_aiosteampy,
    enviar_oferta_aiosteampy,
    registrar_oferta_no_banco,
    validar_dados_requisicao,
)
from models import InformacoesPagamento
from app import db
import asyncio

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

    pagamento = dados.get('pagamento')
    if not pagamento:
        return jsonify({"erro": "Dados de pagamento ausentes"}), 400

    # Atualiza ou cria informações de pagamento
    info_pagamento = InformacoesPagamento.query.filter_by(steamid=str(partner_steamid64)).first()
    if not info_pagamento:
        info_pagamento = InformacoesPagamento(steamid=str(partner_steamid64))

    info_pagamento.tradelink = tradelink
    info_pagamento.metodo_pagamento = pagamento.get('metodo_pagamento')

    if pagamento['metodo_pagamento'] == 'pix':
        info_pagamento.chave_pix = pagamento.get('chave_pix')
        info_pagamento.banco = info_pagamento.agencia = info_pagamento.conta = info_pagamento.tipo_conta = info_pagamento.carteira = None

    elif pagamento['metodo_pagamento'] == 'transfer':
        info_pagamento.banco = pagamento.get('banco')
        info_pagamento.agencia = pagamento.get('agencia')
        info_pagamento.conta = pagamento.get('conta')
        info_pagamento.tipo_conta = pagamento.get('tipo_conta')
        info_pagamento.chave_pix = info_pagamento.carteira = None

    elif pagamento['metodo_pagamento'] == 'skrill':
        info_pagamento.carteira = pagamento.get('carteira')
        info_pagamento.chave_pix = info_pagamento.banco = info_pagamento.agencia = info_pagamento.conta = info_pagamento.tipo_conta = None

    else:
        return jsonify({"erro": "Método de pagamento inválido"}), 400

    db.session.add(info_pagamento)
    db.session.commit()
    print("💾 Informações de pagamento salvas no banco.")

    async def processar_oferta():
        try:
            client = await realizar_login_aiosteampy()
            print("✅ Login com aiosteampy realizado com sucesso.")

            try:
                offer_id = await enviar_oferta_aiosteampy(client, tradelink, [item["assetid"] for item in itens_selecionados])
                print(f"🎉 Oferta enviada com sucesso! ID: {offer_id}")
                registrar_oferta_no_banco(offer_id, partner_steamid64)
                print("💾 Oferta registrada com sucesso no banco.")
            finally:
                await client.logout()
                print("👋 Cliente desconectado após envio.")

            return jsonify({
                "mensagem": "Oferta criada com sucesso!",
                "offer_id": offer_id
            }), 200

        except Exception as e:
            print(f"Erro interno: {e}")
            return jsonify({"erro": f"Erro interno: {str(e)}"}), 500

    return asyncio.run(processar_oferta())
