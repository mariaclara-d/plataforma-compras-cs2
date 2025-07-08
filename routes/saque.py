from flask import Blueprint, request, jsonify
from models.saques import Saque
from db_config import db
from services.saldo_service import calcular_saldo_usuario
from twilio.rest import Client
import os

bp = Blueprint('saque_sistema', __name__)

@bp.route('/saque', methods=['POST'])
def solicitar_saque():
    data = request.json
    steamid = data.get('steamid')
    valor = float(data.get('valor', 0))

    if not steamid or valor <= 0:
        return jsonify({'erro': 'Dados inválidos'}), 400

    saldo = calcular_saldo_usuario(steamid)
    if valor > saldo:
        return jsonify({'erro': 'Saldo insuficiente'}), 400

    saque = Saque(steamid=steamid, valor=valor)
    db.session.add(saque)
    db.session.commit()

    # --- Notificação via WhatsApp (Twilio) - texto livre ---
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
            print(f"WhatsApp enviado! SID: {message.sid}")
        except Exception as e:
            print(f"Erro ao enviar WhatsApp: {e}")
    # -----------------------------------------------------

    return jsonify({'mensagem': 'Solicitação de saque registrada', 'id': saque.id})