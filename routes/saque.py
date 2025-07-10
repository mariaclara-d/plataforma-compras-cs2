from flask import Blueprint, request, jsonify, session, current_app
from models.saques import Saque
from db_config import db
from services.saldo_service import calcular_saldo_usuario
from twilio.rest import Client
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
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    whatsapp_from = os.getenv('TWILIO_WHATSAPP_FROM')
    whatsapp_to = os.getenv('TWILIO_WHATSAPP_TO')
    if account_sid and auth_token and whatsapp_from and whatsapp_to:
        try:
            client = Client(account_sid, auth_token)
            mensagem = f"Novo saque solicitado!\nUsuário: {steamid}\nValor: R$ {valor:.2f}"
            message = client.messages.create(
                body=mensagem,
                from_=whatsapp_from,
                to=whatsapp_to
            )
            current_app.logger.info(f"WhatsApp enviado! SID: {message.sid}")
        except Exception as e:
            current_app.logger.error(f"Erro ao enviar WhatsApp: {e}")
    # -----------------------------------------

    return jsonify({'mensagem': 'Solicitação de saque registrada', 'id': saque.id})