from flask import Blueprint, request, jsonify, session, current_app
from flask_wtf.csrf import validate_csrf, CSRFError
from services.aiosteampy_service import (
    realizar_login_aiosteampy,
    enviar_oferta_aiosteampy,
    registrar_oferta_no_banco,
    validar_dados_requisicao,
)
from services.inventory_service import InventoryService
from models import InformacoesPagamento
from app import db
import asyncio
import traceback

trade_blueprint = Blueprint('trade', __name__, template_folder="../templates")

# Initialize inventory service
inventory_service = InventoryService()

def login_required_api(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'steam_id' not in session:
            return jsonify({"erro": "Usuário não autenticado"}), 401
        return f(*args, **kwargs)
    return decorated

@trade_blueprint.route('/enviar-oferta', methods=['POST'])
@login_required_api
def enviar_oferta_com_aiosteampy():
    current_app.logger.info("===> Entrou no endpoint /enviar-oferta")
    try:
        current_app.logger.info(f"Payload recebido: {request.json}")

        dados = request.json

        try:
            csrf_token = request.headers.get('X-CSRFToken') or dados.get('csrf_token')
            validate_csrf(csrf_token)
        except CSRFError as e:
            current_app.logger.info(f"CSRF inválido: {e.description}")
            return jsonify({"erro": "CSRF token inválido"}), 403

        try:
            itens_selecionados, tradelink, partner_steamid64 = validar_dados_requisicao(dados)
        except Exception as e:
            msg = str(e) or "Erro de validação nos dados enviados."
            current_app.logger.error(f"Erro ao validar dados: {msg}")
            return jsonify({"erro": msg}), 400

        # Garante que o usuário só envie oferta do próprio inventário
        if str(partner_steamid64) != str(session.get('steam_id')):
            return jsonify({"erro": "Operação não autorizada"}), 403

        # VALIDAÇÃO DE ASSETIDS - Verificar se os itens selecionados são válidos
        current_app.logger.info("Iniciando validação de assetids...")
        selected_assetids = [item["assetid"] for item in itens_selecionados]
        current_app.logger.info(f"AssetIDs selecionados para validação: {selected_assetids}")
        
        validation_result = inventory_service.validate_selected_items(selected_assetids, str(partner_steamid64))
        
        if not validation_result['valid']:
            current_app.logger.error(f"Validação de assetids falhou: {validation_result['error']}")
            return jsonify({
                "erro": f"Itens inválidos selecionados: {validation_result['invalid_items']}",
                "detalhes": "Os itens podem ter sido vendidos ou não estão mais disponíveis no seu inventário."
            }), 400
        
        current_app.logger.info(f"Validação de assetids bem-sucedida - {len(validation_result['valid_items'])} itens válidos")

        pagamento = dados.get('pagamento')
        if not pagamento:
            return jsonify({"erro": "Dados de pagamento ausentes"}), 400

        metodo = pagamento.get('metodo_pagamento')
        if metodo not in {'pix', 'transfer', 'skrill'}:
            return jsonify({"erro": "Método de pagamento inválido"}), 400

        # Validação básica dos campos de pagamento
        if metodo == 'pix' and not pagamento.get('chave_pix'):
            return jsonify({"erro": "Chave PIX obrigatória"}), 400
        if metodo == 'transfer' and not all([pagamento.get('banco'), pagamento.get('agencia'), pagamento.get('conta'), pagamento.get('tipo_conta')]):
            return jsonify({"erro": "Dados bancários incompletos"}), 400
        if metodo == 'skrill' and not pagamento.get('carteira'):
            return jsonify({"erro": "Carteira Skrill obrigatória"}), 400

        # Atualiza ou cria informações de pagamento
        info_pagamento = InformacoesPagamento.query.filter_by(steamid=str(partner_steamid64)).first()
        if not info_pagamento:
            info_pagamento = InformacoesPagamento(steamid=str(partner_steamid64))

        info_pagamento.tradelink = tradelink
        info_pagamento.metodo_pagamento = metodo

        if metodo == 'pix':
            info_pagamento.chave_pix = pagamento.get('chave_pix')
            info_pagamento.banco = info_pagamento.agencia = info_pagamento.conta = info_pagamento.tipo_conta = info_pagamento.carteira = None
        elif metodo == 'transfer':
            info_pagamento.banco = pagamento.get('banco')
            info_pagamento.agencia = pagamento.get('agencia')
            info_pagamento.conta = pagamento.get('conta')
            info_pagamento.tipo_conta = pagamento.get('tipo_conta')
            info_pagamento.chave_pix = info_pagamento.carteira = None
        elif metodo == 'skrill':
            info_pagamento.carteira = pagamento.get('carteira')
            info_pagamento.chave_pix = info_pagamento.banco = info_pagamento.agencia = info_pagamento.conta = info_pagamento.tipo_conta = None

        db.session.add(info_pagamento)
        db.session.commit()
        current_app.logger.info("Informações de pagamento salvas no banco.")

        async def processar_oferta():
            try:
                client = await realizar_login_aiosteampy()
                current_app.logger.info("Login com aiosteampy realizado com sucesso.")

                try:
                    offer_id = await enviar_oferta_aiosteampy(client, tradelink, [item["assetid"] for item in itens_selecionados])
                    current_app.logger.info(f"Oferta enviada com sucesso! ID: {offer_id}")
                    
                    # Registrar a oferta no banco agora (movido para cá)
                    registrar_oferta_no_banco(offer_id, partner_steamid64, [item["assetid"] for item in itens_selecionados])
                    current_app.logger.info("Oferta registrada com sucesso no banco.")
                finally:
                    await client.logout()
                    current_app.logger.info("Cliente desconectado após envio.")

                return jsonify({
                    "mensagem": "Oferta criada com sucesso!",
                    "offer_id": offer_id
                }), 200

            except Exception as e:
                import traceback
                current_app.logger.error(f"🚨 ERRO DETALHADO: {type(e).__name__}: {str(e)}")
                current_app.logger.error(f"🚨 TRACEBACK COMPLETO:")
                current_app.logger.error(traceback.format_exc())
                
                # Desconectar cliente se ainda conectado
                try:
                    await client.logout()
                    current_app.logger.info("Cliente desconectado após erro.")
                except:
                    pass
                
                return jsonify({"erro": f"Erro interno: {str(e)}"}), 500

        return asyncio.run(processar_oferta())

    except Exception as e:
        current_app.logger.error(f"Erro inesperado: {e}")
        current_app.logger.error(traceback.format_exc())
        return jsonify({"erro": "Erro inesperado no servidor."}), 500