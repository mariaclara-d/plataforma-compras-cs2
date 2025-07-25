from flask import Blueprint, request, jsonify, session, current_app
from models.saques import Saque
from db_config import db
from services.saldo_service import calcular_saldo_usuario
from services.notification_service import notification_service
import os

bp = Blueprint('saque_sistema', __name__)

def login_required_api(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'steam_id' not in session:
            return jsonify({'erro': 'Usuário não autenticado'}), 401
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
        return jsonify({'erro': 'Valor inválido'}), 400

    # Garante que o usuário só saque do próprio saldo
    if steamid != session.get('steam_id'):
        return jsonify({'erro': 'Operação não autorizada'}), 403

    if not steamid or valor <= 0:
        return jsonify({'erro': 'Dados inválidos'}), 400

    saldo = calcular_saldo_usuario(steamid)
    if valor > saldo:
        return jsonify({'erro': 'Saldo insuficiente'}), 400

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