from flask import Blueprint, request, jsonify, session, current_app
from models.saques import Saque
from db_config import db
from services.saldo_service import calcular_saldo_usuario
from services.notification_service import notification_service
from services.trade_hold_service import TradeHoldService
import os

bp = Blueprint('saque_sistema', __name__)

def login_required_api(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'steam_id' not in session:
            return jsonify({'error': 'User not authenticated'}), 401
        return f(*args, **kwargs)
    return decorated

@bp.route('/saque', methods=['POST'])
@login_required_api
def solicitar_saque():
    data = request.json
    steamid = data.get('steamid')
    try:
        valor = float(data.get('valor', 0))
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid amount'}), 400

    # Garante que o usuário só saque do próprio saldo
    if steamid != session.get('steam_id'):
        return jsonify({'error': 'Unauthorized operation'}), 403

    if not steamid or valor <= 0:
        return jsonify({'error': 'Invalid data'}), 400

    # Verificar saldo total
    saldo = calcular_saldo_usuario(steamid)
    if valor > saldo:
        return jsonify({'error': 'Insufficient balance'}), 400
    
    # VERIFICAÇÃO DE TRADE HOLD - Novo sistema
    try:
        # Obter informações de saldo disponível (excluindo valores em hold)
        balance_info = TradeHoldService.get_user_available_balance(steamid)
        
        # Verificar se pode sacar o valor solicitado
        if not TradeHoldService.can_withdraw_amount(steamid, valor):
            return jsonify({
                'error': 'Balance blocked by Trade Protection',
                'details': {
                    'total_balance': balance_info['saldo_total'],
                    'amount_on_hold': balance_info['valor_em_hold'],
                    'available_balance': balance_info['saldo_disponivel'],
                    'requested_amount': valor,
                    'trade_protection_info': TradeHoldService.get_user_hold_info(steamid)
                }
            }), 400
            
    except Exception as e:
        current_app.logger.error(f"Erro ao verificar trade holds: {e}")
        return jsonify({'error': 'Internal error in protection system'}), 500

    saque = Saque(steamid=steamid, valor=valor)
    db.session.add(saque)
    db.session.commit()

    # --- Notificação via WhatsApp (Twilio) ---
    try:
        # Buscar informações de pagamento do usuário (se disponível)
        from models import InformacoesPagamento
        info_pagamento = InformacoesPagamento.query.filter_by(steamid=steamid).first()
        
        metodo_pagamento = 'PIX'
        chave_pix = 'Não informado'
        
        if info_pagamento:
            metodo_pagamento = info_pagamento.metodo_pagamento or 'PIX'
            chave_pix = info_pagamento.chave_pix or 'Não informado'
        
        # Enviar notificação usando o serviço
        notification_service.enviar_notificacao_saque(
            usuario_nome=f"SteamID: {steamid}",
            valor=valor,
            metodo_pagamento=metodo_pagamento,
            chave_pix=chave_pix
        )
        
        current_app.logger.info("✅ Notificação de saque enviada com sucesso")
    except Exception as e:
        current_app.logger.error(f"❌ Erro ao enviar notificação de saque: {e}")
    # -----------------------------------------

    return jsonify({'mensagem': 'Solicitação de saque registrada', 'id': saque.id})