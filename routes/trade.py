from flask import Blueprint, request, jsonify, session, current_app
from flask_wtf.csrf import validate_csrf, CSRFError
from services.aiosteampy_service import (
    realizar_login_aiosteampy,
    enviar_oferta_aiosteampy,
    registrar_oferta_no_banco,
    validar_dados_requisicao,
)
from services.inventory_service import InventoryService
from services.notification_service import notification_service
from services.security_service import SecurityService
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
    """Envia oferta de trade usando aiosteampy com validações de segurança"""
    current_app.logger.info("===> Entrou no endpoint /enviar-oferta")
    
    # RATE LIMITING
    client_id = SecurityService.get_client_identifier()
    if not SecurityService.check_rate_limit(client_id, max_requests=5, window_seconds=60):
        SecurityService.log_security_event("RATE_LIMIT_EXCEEDED", {
            "client_id": client_id,
            "endpoint": "/trade/enviar-oferta"
        })
        return jsonify({"erro": "Muitas tentativas. Tente novamente em 1 minuto."}), 429
    
    try:
        current_app.logger.info(f"Payload recebido: {request.json}")

        dados = request.json

        # CSRF VALIDATION
        try:
            csrf_token = request.headers.get('X-CSRFToken') or dados.get('csrf_token')
            validate_csrf(csrf_token)
        except CSRFError as e:
            SecurityService.log_security_event("CSRF_INVALID", {
                "error": str(e),
                "client_id": client_id
            })
            current_app.logger.info(f"CSRF inválido: {e.description}")
            return jsonify({"erro": "CSRF token inválido"}), 403

        # BASIC DATA VALIDATION
        try:
            itens_selecionados, tradelink, partner_steamid64 = validar_dados_requisicao(dados)
        except Exception as e:
            SecurityService.log_security_event("INVALID_REQUEST_DATA", {
                "error": str(e),
                "client_id": client_id
            })
            msg = str(e) or "Erro de validação nos dados enviados."
            current_app.logger.error(f"Erro ao validar dados: {msg}")
            return jsonify({"erro": msg}), 400

        # ADDITIONAL SECURITY VALIDATIONS
        if not SecurityService.validate_steam_id(str(partner_steamid64)):
            SecurityService.log_security_event("INVALID_STEAM_ID", {
                "steam_id": str(partner_steamid64),
                "client_id": client_id
            })
            return jsonify({"erro": "SteamID inválido"}), 400
        
        if not SecurityService.validate_tradelink(tradelink):
            SecurityService.log_security_event("INVALID_TRADELINK", {
                "tradelink": tradelink[:50] + "...",  # Log parcial por segurança
                "client_id": client_id
            })
            return jsonify({"erro": "Trade link inválido"}), 400

        # Garante que o usuário só envie oferta do próprio inventário
        if str(partner_steamid64) != str(session.get('steam_id')):
            SecurityService.log_security_event("UNAUTHORIZED_TRADE", {
                "partner_steamid64": str(partner_steamid64),
                "session_steam_id": str(session.get('steam_id')),
                "client_id": client_id
            })
            return jsonify({"erro": "Operação não autorizada"}), 403

        # VALIDAÇÃO DE ASSETIDS COM SECURITY SERVICE
        current_app.logger.info("Iniciando validação de assetids...")
        selected_assetids = [item["assetid"] for item in itens_selecionados]
        
        # Validar formato dos AssetIDs
        for assetid in selected_assetids:
            if not SecurityService.validate_assetid(assetid):
                SecurityService.log_security_event("INVALID_ASSETID", {
                    "assetid": assetid,
                    "client_id": client_id
                })
                return jsonify({"erro": f"Asset ID inválido: {assetid}"}), 400
        
        current_app.logger.info(f"AssetIDs selecionados para validação: {selected_assetids}")
        
        validation_result = inventory_service.validate_selected_items(selected_assetids, str(partner_steamid64))
        
        if not validation_result['valid']:
            SecurityService.log_security_event("INVALID_ITEMS_SELECTED", {
                "invalid_items": validation_result['invalid_items'],
                "client_id": client_id
            })
            current_app.logger.error(f"Validação de assetids falhou: {validation_result['error']}")
            return jsonify({
                "erro": f"Itens inválidos selecionados: {validation_result['invalid_items']}",
                "detalhes": "Os itens podem ter sido vendidos ou não estão mais disponíveis no seu inventário."
            }), 400
        
        current_app.logger.info(f"Validação de assetids bem-sucedida - {len(validation_result['valid_items'])} itens válidos")

        # VALIDAÇÃO DE DADOS DE PAGAMENTO COM SECURITY SERVICE
        pagamento = dados.get('pagamento')
        payment_validation = SecurityService.validate_payment_data(pagamento)
        
        if not payment_validation['valid']:
            SecurityService.log_security_event("INVALID_PAYMENT_DATA", {
                "error": payment_validation['error'],
                "client_id": client_id
            })
            return jsonify({"erro": payment_validation['error']}), 400
        
        # Usar dados sanitizados
        pagamento_sanitizado = payment_validation['sanitized_data']

        # Atualiza ou cria informações de pagamento usando dados sanitizados
        info_pagamento = InformacoesPagamento.query.filter_by(steamid=str(partner_steamid64)).first()
        if not info_pagamento:
            info_pagamento = InformacoesPagamento(steamid=str(partner_steamid64))

        info_pagamento.tradelink = tradelink
        info_pagamento.metodo_pagamento = pagamento_sanitizado['metodo_pagamento']

        if pagamento_sanitizado['metodo_pagamento'] == 'pix':
            info_pagamento.chave_pix = pagamento_sanitizado.get('chave_pix')
            info_pagamento.banco = info_pagamento.agencia = info_pagamento.conta = info_pagamento.tipo_conta = info_pagamento.carteira = None
        elif pagamento_sanitizado['metodo_pagamento'] == 'transfer':
            info_pagamento.banco = pagamento_sanitizado.get('banco')
            info_pagamento.agencia = pagamento_sanitizado.get('agencia')
            info_pagamento.conta = pagamento_sanitizado.get('conta')
            info_pagamento.tipo_conta = pagamento_sanitizado.get('tipo_conta')
            info_pagamento.chave_pix = info_pagamento.carteira = None
        elif pagamento_sanitizado['metodo_pagamento'] == 'skrill':
            info_pagamento.carteira = pagamento_sanitizado.get('carteira')
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
                    
                    # Enviar notificação WhatsApp
                    try:
                        # Calcular valor total dos itens
                        valor_total = sum([
                            float(item.get('price', 0)) for item in itens_selecionados
                        ])
                        
                        # Enviar notificação
                        notification_service.enviar_notificacao_trade_oferta(
                            usuario_nome=session.get('steam_username', f"SteamID: {session.get('steam_id', 'N/A')}"),
                            valor_total=valor_total,
                            itens_count=len(itens_selecionados),
                            offer_id=offer_id
                        )
                        current_app.logger.info("✅ Notificação WhatsApp enviada com sucesso")
                    except Exception as notification_error:
                        # Log do erro mas não quebrar o fluxo
                        current_app.logger.error(f"❌ Erro ao enviar notificação WhatsApp: {notification_error}")
                    
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