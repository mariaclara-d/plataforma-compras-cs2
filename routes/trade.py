from flask import Blueprint, request, jsonify, session, current_app
from flask_wtf.csrf import validate_csrf, CSRFError
from services.aiosteampy_service import (
    enviar_oferta_principal,
    registrar_oferta_no_banco,
    validar_dados_requisicao,
)
from services.inventory_service import InventoryService
from services.notification_service import notification_service
from services.security_service import SecurityService
from services.trade_hold_service import TradeHoldService
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
                # Sistema de retry inteligente para erros temporários da Steam
                max_tentativas = 5  # Aumentar para 5 tentativas
                tentativa_atual = 1
                offer_id = None
                retry_error = None
                
                while tentativa_atual <= max_tentativas:
                    try:
                        current_app.logger.info(f"🔄 Tentativa {tentativa_atual}/{max_tentativas} de enviar oferta...")
                        
                        # Preparar dados para a nova assinatura da função
                        items_dict = {
                            "tradelink": tradelink,
                            "items": [{"assetid": item["assetid"]} for item in itens_selecionados]
                        }
                        
                        result = await enviar_oferta_principal(partner_steamid64, items_dict)
                        
                        current_app.logger.info(f"🔍 RESULTADO COMPLETO: {result}")
                        current_app.logger.info(f"🔍 TIPO DO RESULTADO: {type(result)}")
                        current_app.logger.info(f"🔍 CHAVES DISPONÍVEIS: {list(result.keys()) if isinstance(result, dict) else 'N/A'}")
                        
                        if result.get("success"):
                            offer_id = result.get("tradeoffer_id")
                            if not offer_id:
                                # Tentar chaves alternativas que podem vir da Steam
                                offer_id = result.get("trade_offer_id") or result.get("offerid") or result.get("id")
                            
                            if offer_id:
                                current_app.logger.info(f"✅ Oferta enviada com sucesso! ID: {offer_id}")
                                break  # Sucesso, sair do loop
                            else:
                                error_message = "❌ ERRO: Steam não retornou Trade Offer ID válido"
                                current_app.logger.error(error_message)
                                current_app.logger.error(f"❌ RESULTADO COMPLETO: {result}")
                                raise RuntimeError(error_message)
                        else:
                            # Se não foi sucesso, tratar como erro
                            error_message = result.get("message", "Erro desconhecido")
                            current_app.logger.error(f"❌ ERRO RETORNADO: {error_message}")
                            current_app.logger.error(f"❌ RESULTADO COMPLETO DO ERRO: {result}")
                            raise RuntimeError(error_message)
                        
                    except Exception as e:
                        error_msg = str(e)
                        retry_error = e
                        
                        # Determinar se deve tentar novamente
                        should_retry = False
                        wait_time = 0
                        
                        if ("Steam temporariamente indisponível" in error_msg or 
                            "Erro da Steam (500)" in error_msg or
                            "500" in error_msg and "Internal Server Error" in error_msg or
                            "Steam temporariamente indisponível (HTTP 500)" in error_msg):
                            # Erro 500 da Steam - retry com backoff exponencial mais conservador
                            should_retry = True
                            wait_time = min(tentativa_atual * 15, 90)  # 15s, 30s, 45s, até 90s max
                            current_app.logger.warning(f"🕐 Steam indisponível (tentativa {tentativa_atual}). Aguardando {wait_time}s...")
                        elif "Rate limit" in error_msg or "429" in error_msg:
                            # Rate limit - retry com espera maior
                            should_retry = True
                            wait_time = 30 + (tentativa_atual * 15)  # 45s, 60s, 75s...
                            current_app.logger.warning(f"⏳ Rate limit da Steam (tentativa {tentativa_atual}). Aguardando {wait_time}s...")
                        elif "Timeout" in error_msg or "timeout" in error_msg.lower():
                            # Timeout - retry rápido
                            should_retry = True
                            wait_time = tentativa_atual * 5  # 5s, 10s, 15s...
                            current_app.logger.warning(f"⏱️ Timeout da Steam (tentativa {tentativa_atual}). Aguardando {wait_time}s...")
                        elif "rede" in error_msg.lower() or "network" in error_msg.lower():
                            # Problema de rede - retry moderado
                            should_retry = True
                            wait_time = tentativa_atual * 8  # 8s, 16s, 24s...
                            current_app.logger.warning(f"🌐 Problema de rede (tentativa {tentativa_atual}). Aguardando {wait_time}s...")
                        
                        # Se deve tentar novamente e ainda tem tentativas
                        if should_retry and tentativa_atual < max_tentativas:
                            import asyncio
                            await asyncio.sleep(wait_time)
                            tentativa_atual += 1
                            continue
                        else:
                            # Erro definitivo ou esgotaram tentativas
                            current_app.logger.error(f"❌ Falha após {tentativa_atual} tentativas: {error_msg}")
                            raise retry_error
                
                # Verificar se a oferta foi enviada com sucesso
                if not offer_id:
                    raise retry_error or Exception("Falha ao enviar oferta após todas as tentativas")
                    
                # Registrar a oferta no banco após sucesso
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
                
                # ===== NOVO: CRIAR TRADE HOLD PARA PROTEÇÃO DE 7 DIAS =====
                try:
                    # Calcular valor total dos itens vendidos
                    valor_total = sum([float(item.get('price', 0)) for item in itens_selecionados])
                    
                    # Lista de nomes dos itens para o hold
                    nomes_itens = [item.get('market_hash_name', 'Item desconhecido') for item in itens_selecionados]
                    descricao_itens = f"{len(nomes_itens)} item(s): {', '.join(nomes_itens[:3])}"
                    if len(nomes_itens) > 3:
                        descricao_itens += f" e mais {len(nomes_itens) - 3}..."
                    
                    # Criar hold usando o offer_id como transacao_id (temporário)
                    # Em uma implementação completa, você criaria uma transação real primeiro
                    hold = TradeHoldService.create_hold_for_transaction(
                        user_id=session.get('steam_id'),
                        transacao_id=offer_id,  # Usando offer_id temporariamente
                        valor=valor_total,
                        item_name=descricao_itens
                    )
                    
                    current_app.logger.info(f"✅ Trade Hold criado: ID {hold.id}, Valor: R$ {valor_total}, Expira em: {hold.expires_at}")
                    
                except Exception as hold_error:
                    # Log do erro mas não quebrar o fluxo principal
                    current_app.logger.error(f"❌ Erro ao criar Trade Hold: {hold_error}")
                    # A venda continua mesmo se o hold falhar
                # =========================================================
                
                # Obter informações de hold para retornar ao usuário
                hold_info = None
                try:
                    user_hold_info = TradeHoldService.get_user_hold_info(session.get('steam_id'))
                    if user_hold_info:
                        hold_info = {
                            'total_em_hold': user_hold_info['balance_info']['valor_em_hold'],
                            'saldo_disponivel': user_hold_info['balance_info']['saldo_disponivel'],
                            'holds_ativos': len(user_hold_info['active_holds'])
                        }
                except Exception as e:
                    current_app.logger.error(f"Erro ao obter info de hold: {e}")

                return jsonify({
                    "mensagem": "Oferta criada com sucesso!",
                    "offer_id": offer_id,
                    "trade_protection": {
                        "ativo": True,
                        "periodo_dias": 7,
                        "mensagem": "Seus itens estão protegidos por 7 dias. Você pode reverter a venda durante este período.",
                        "hold_info": hold_info
                    }
                }), 200

            except Exception as e:
                import traceback
                current_app.logger.error(f"🚨 ERRO DETALHADO: {type(e).__name__}: {str(e)}")
                current_app.logger.error(f"🚨 TRACEBACK COMPLETO:")
                current_app.logger.error(traceback.format_exc())
                
                # Tratar erros específicos para o usuário
                error_message = str(e)
                
                if ("Steam temporariamente indisponível" in error_message or 
                    "Erro da Steam (500)" in error_message or
                    ("500" in error_message and "Internal Server Error" in error_message)):
                    return jsonify({
                        "erro": "🕐 Steam indisponível temporariamente",
                        "detalhes": "Os servidores da Steam estão com instabilidade. Este é um problema da própria Steam, não da nossa plataforma. Tente novamente em 10-15 minutos.",
                        "tipo": "steam_server_error",
                        "retry_sugestao": "Aguarde 10-15 minutos e tente novamente",
                        "codigo_steam": "500"
                    }), 503
                elif "Erro de autenticação" in error_message or "🔐" in error_message:
                    return jsonify({
                        "erro": "🔒 Problema de autenticação Steam",
                        "detalhes": "Problema temporário com o bot da Steam. Nossa equipe foi notificada.",
                        "tipo": "steam_auth_error",
                        "contato_suporte": True
                    }), 401
                elif "Rate limit" in error_message or "⏳" in error_message:
                    return jsonify({
                        "erro": "⏳ Limite de requisições atingido",
                        "detalhes": "A Steam está limitando as requisições. Aguarde 30 minutos antes de tentar novamente.",
                        "tipo": "rate_limit_error",
                        "retry_sugestao": "Aguarde 30 minutos"
                    }), 429
                elif "Timeout" in error_message or "⏱️" in error_message:
                    return jsonify({
                        "erro": "⏱️ Timeout na conexão com Steam",
                        "detalhes": "A Steam demorou muito para responder. Tente novamente em alguns minutos.",
                        "tipo": "timeout_error",
                        "retry_sugestao": "Tente novamente em 5 minutos"
                    }), 504
                elif "rede" in error_message.lower() or "network" in error_message.lower():
                    return jsonify({
                        "erro": "🌐 Problema de conectividade",
                        "detalhes": "Problema temporário de rede com a Steam. Tente novamente em alguns minutos.",
                        "tipo": "network_error",
                        "retry_sugestao": "Tente novamente em 2-5 minutos"
                    }), 502
                else:
                    return jsonify({
                        "erro": "⚠️ Erro inesperado",
                        "detalhes": f"Ocorreu um erro técnico: {error_message[:200]}...",
                        "tipo": "general_error",
                        "contato_suporte": True
                    }), 500
                
                return jsonify({"erro": f"Erro interno: {str(e)}"}), 500

        return asyncio.run(processar_oferta())

    except Exception as e:
        current_app.logger.error(f"Erro inesperado: {e}")
        current_app.logger.error(traceback.format_exc())
        return jsonify({"erro": "Erro inesperado no servidor."}), 500