from flask import Blueprint, request, jsonify, session, current_app
from flask_wtf.csrf import validate_csrf, CSRFError
from services.inventory_service import InventoryService
from services.notification_service import notification_service
from services.security_service import SecurityService
from services.trade_hold_service import TradeHoldService
from services.steam_utils import validar_dados_requisicao, calcular_valor_liquido
from services.steamwebapi_service import enviar_oferta_steamwebapi
from models import InformacoesPagamento
from models import TradeOffer, Skin, Saldo, TradeHold, Transacao
from db_config import db
from decimal import Decimal
from datetime import datetime
from datetime import datetime, timezone, timedelta
import time
from app import db
import asyncio
import traceback
import os

trade_blueprint = Blueprint('trade', __name__, template_folder="../templates")

# Initialize inventory service
inventory_service = InventoryService()

def login_required_api(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'steam_id' not in session:
            return jsonify({"error": "User not authenticated"}), 401
        return f(*args, **kwargs)
    return decorated

@trade_blueprint.route('/enviar-oferta', methods=['POST'])
@login_required_api
def enviar_oferta_steamwebapi():
    """Envia oferta de trade usando SteamWebAPI com validações de segurança"""
    current_app.logger.info("===> Entrou no endpoint /enviar-oferta")
    
    # RATE LIMITING
    client_id = SecurityService.get_client_identifier()
    if not SecurityService.check_rate_limit(client_id, max_requests=5, window_seconds=60):
        SecurityService.log_security_event("RATE_LIMIT_EXCEEDED", {
            "client_id": client_id,
            "endpoint": "/trade/enviar-oferta"
        })
        return jsonify({"error": "Too many attempts. Please try again in 1 minute."}), 429
    
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
            return jsonify({"error": "Invalid CSRF token"}), 403

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
            return jsonify({"error": msg}), 400

        # ADDITIONAL SECURITY VALIDATIONS
        if not SecurityService.validate_steam_id(str(partner_steamid64)):
            SecurityService.log_security_event("INVALID_STEAM_ID", {
                "steam_id": str(partner_steamid64),
                "client_id": client_id
            })
            return jsonify({"error": "Invalid Steam ID"}), 400
        
        if not SecurityService.validate_tradelink(tradelink):
            SecurityService.log_security_event("INVALID_TRADELINK", {
                "tradelink": tradelink[:50] + "...",  # Log parcial por segurança
                "client_id": client_id
            })
            return jsonify({"error": "Invalid trade link"}), 400

        # Garante que o usuário só envie oferta do próprio inventário
        if str(partner_steamid64) != str(session.get('steam_id')):
            SecurityService.log_security_event("UNAUTHORIZED_TRADE", {
                "partner_steamid64": str(partner_steamid64),
                "session_steam_id": str(session.get('steam_id')),
                "client_id": client_id
            })
            return jsonify({"error": "Unauthorized operation"}), 403

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
                return jsonify({"error": f"Invalid Asset ID: {assetid}"}), 400
        
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
            return jsonify({"error": payment_validation['error']}), 400
        
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
                # Calcular valor (usando steam_utils)
                valor_total = sum(calcular_valor_liquido(item.get('price', 0)) for item in itens_selecionados)
                
                # CHAMAR STEAMWEBAPI
                current_app.logger.info("[MAIN] === USANDO STEAMWEBAPI OFICIAL ===")
                
                items_dict = {
                    "tradelink": tradelink,
                    "itens": [{"assetid": item["assetid"]} for item in itens_selecionados]
                }
                
                resultado_steamwebapi = await enviar_oferta_steamwebapi(
                    partner_steamid64, 
                    items_dict, 
                    f"Venda para {os.getenv('COMPANY_NAME', 'Nossa Empresa')} - {len(itens_selecionados)} item(s) - Você receberá o pagamento via PIX após aceitar"
                )
                
                if resultado_steamwebapi.get('success'):
                    current_app.logger.info("[SUCCESS] 🎉 Trade offer criada via SteamWebAPI!")
                    
                    # ===== CRÍTICO: PERSISTIR DADOS NO BANCO =====
                    try:
                        trade_offer_id = resultado_steamwebapi.get('tradeoffer_id')
                        current_app.logger.info(f"[DATABASE] Salvando trade offer ID: {trade_offer_id}")
                        
                        # 1. CRIAR TradeOffer no banco
                        trade_offer = TradeOffer(
                            tradeofferid=trade_offer_id,
                            partner_steam_id=partner_steamid64,
                            status='pendente',  # Status inicial: aguardando aceitação do usuário
                            is_our_offer=True,
                            criado_em=datetime.now(timezone.utc)
                        )
                        db.session.add(trade_offer)
                        db.session.flush()  # Para obter o ID
                        
                        current_app.logger.info(f"[DATABASE] ✅ TradeOffer criado: ID={trade_offer.id}")
                        
                        # 2. CRIAR registros de Skin para cada item
                        valor_total = Decimal('0.00')
                        skins_criadas = []
                        
                        for item in itens_selecionados:
                            # Calcular valores com precisão decimal
                            preco_bruto = Decimal(str(item.get('price_safe', '0')))
                            valor_liquido = Decimal(str(calcular_valor_liquido(preco_bruto)))
                            
                            skin = Skin(
                                nome=item.get('name', 'Item desconhecido'),
                                preco=preco_bruto,
                                valor_liquido=valor_liquido,
                                assetid=item.get('assetid'),
                                classid=item.get('classid'),
                                instanceid=item.get('instanceid', '0'),
                                tradeofferid=trade_offer_id,
                                criado_em=datetime.now(timezone.utc)
                            )
                            db.session.add(skin)
                            skins_criadas.append(skin)
                            valor_total += valor_liquido
                        
                        current_app.logger.info(f"[DATABASE] ✅ {len(skins_criadas)} Skins criadas, valor total: R$ {valor_total}")
                        
                        # 3. ATUALIZAR Saldo do usuário (usando método do modelo)
                        Saldo.criar_ou_atualizar_saldo(partner_steamid64, valor_total)
                        current_app.logger.info(f"[DATABASE] ✅ Saldo atualizado para usuário {partner_steamid64}")
                        
                        # 4. CRIAR TradeHold para proteção de 7 dias
                        # Criar transação primeiro para referenciar no hold
                        transacao = Transacao(
                            steamid=partner_steamid64,
                            valor=valor_total,
                            tipo='venda_skin',
                            status='pendente',
                            criado_em=datetime.now(timezone.utc)
                        )
                        db.session.add(transacao)
                        db.session.flush()
                        
                        # Criar o hold referenciando a transação
                        trade_hold = TradeHold(
                            steam_id=partner_steamid64,
                            transacao_id=transacao.id,
                            valor=valor_total,
                            item_name=f"{len(skins_criadas)} itens CS2",
                            status='active',
                            criado_em=datetime.now(timezone.utc)
                        )
                        db.session.add(trade_hold)
                        current_app.logger.info(f"[DATABASE] ✅ TradeHold criado: proteção 7 dias, valor R$ {valor_total}")
                        
                        # 5. COMMIT todas as alterações
                        db.session.commit()
                        current_app.logger.info("[DATABASE] 🎉 TODAS as alterações confirmadas no banco!")
                        
                        # 6. NOTIFICAR administradores
                        try:
                            notification_service.enviar_notificacao_trade_oferta(
                                usuario_nome=f"SteamID: {partner_steamid64}",
                                valor_total=str(valor_total),
                                itens_count=len(skins_criadas),
                                offer_id=trade_offer_id
                            )
                        except Exception as e:
                            current_app.logger.warning(f"[NOTIFICATION] Erro ao enviar notificação: {e}")
                        
                        # 7. RETORNAR sucesso com dados completos
                        return jsonify({
                            'success': True,
                            'tradeoffer_id': trade_offer_id,
                            'trade_url': f"{os.getenv('STEAM_COMMUNITY_URL', 'https://steamcommunity.com')}/tradeoffer/{trade_offer_id}/",
                            'message': f'Trade offer criada com sucesso! {len(skins_criadas)} itens, valor total: R$ {valor_total:.2f}',
                            'items_count': len(skins_criadas),
                            'total_value': str(valor_total),
                            'protection_info': {
                                'trade_hold_days': 7,
                                'message': 'Seus itens ficarão protegidos por 7 dias após a venda'
                            }
                        })
                        
                    except Exception as db_error:
                        # ROLLBACK em caso de erro no banco
                        db.session.rollback()
                        current_app.logger.error(f"[DATABASE] ❌ Erro ao salvar no banco: {db_error}")
                        current_app.logger.error(f"[DATABASE] ❌ TradeOffer {trade_offer_id} foi criada no Steam mas não salva no banco!")
                        
                        return jsonify({
                            'success': False,
                            'error': 'Trade offer criada no Steam mas erro ao salvar dados',
                            'details': str(db_error),
                            'tradeoffer_id': trade_offer_id,
                            'action_required': 'Contate o suporte informando este ID'
                        }), 500
                    
                else:
                    raise Exception(f"SteamWebAPI falhou: {resultado_steamwebapi.get('error')}")

            except Exception as e:
                current_app.logger.error(f"[STEAMWEBAPI] Erro: {e}")
                return {"success": False, "error": str(e)}

        return asyncio.run(processar_oferta())

    except Exception as e:
        current_app.logger.error(f"Erro inesperado: {e}")
        current_app.logger.error(traceback.format_exc())
        return jsonify({"error": "Unexpected server error."}), 500
