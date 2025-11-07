from flask import Blueprint, request, jsonify, current_app, session
from db_config import db
from models import TradeOffer
from datetime import datetime, timedelta, timezone
from functools import wraps

offer_blueprint = Blueprint('offer', __name__)

def login_required_api(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'steam_id' not in session:
            return jsonify({'error': 'Usuário não autenticado'}), 401
        return f(*args, **kwargs)
    return decorated

@offer_blueprint.route('/create_trade_offer', methods=['POST'])
@login_required_api
def create_trade_offer():
    try:
        data = request.json
        tradeofferid = data.get('tradeofferid')
        partnersteamid = data.get('partnersteamid')

        if not tradeofferid or not partnersteamid:
            return jsonify({'error': 'Campos tradeofferid e partnersteamid são obrigatórios.'}), 400

        if not isinstance(tradeofferid, str) or not isinstance(partnersteamid, str):
            return jsonify({'error': 'Os campos devem ser do tipo string.'}), 400

        # Garante que o usuário só crie oferta para si mesmo
        if str(partnersteamid) != str(session.get('steam_id')):
            return jsonify({'error': 'Operação não autorizada'}), 403

        if not tradeofferid.isdigit() or not partnersteamid.isdigit():
            return jsonify({'error': 'IDs devem ser numéricos.'}), 400

        expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)

        new_offer = TradeOffer(
            tradeofferid=tradeofferid,
            partnersteamid=partnersteamid,
            expires_at=expires_at,
            status='pendente'
        )
        db.session.add(new_offer)
        db.session.commit()

        return jsonify({
            'message': f"Oferta de troca {new_offer.tradeofferid} criada com sucesso!",
            'offer_id': new_offer.id
        }), 201

    except Exception as e:
        current_app.logger.error(f"Erro ao criar oferta: {str(e)}")
        return jsonify({'error': 'Erro interno ao criar oferta.'}), 500

@offer_blueprint.route('/update_trade_offer/<int:offer_id>', methods=['PUT'])
@login_required_api
def update_trade_offer(offer_id):
    try:
        data = request.json
        new_status = data.get('status')

        if not new_status:
            return jsonify({'error': 'Campo status é obrigatório.'}), 400

        allowed_status = {'pendente', 'aceita', 'expirada', 'cancelada', 'recusada'}
        if new_status not in allowed_status:
            return jsonify({'error': 'Status inválido.'}), 400

        offer = TradeOffer.query.get(offer_id)

        if not offer:
            return jsonify({'error': f'Oferta com ID {offer_id} não encontrada.'}), 404

        # Garante que o usuário só atualize oferta própria
        if str(offer.partnersteamid) != str(session.get('steam_id')):
            return jsonify({'error': 'Operação não autorizada'}), 403

        offer.status = new_status
        db.session.commit()

        return jsonify({
            'message': f"Status da oferta {offer.tradeofferid} atualizado para {offer.status}!"
        }), 200

    except Exception as e:
        current_app.logger.error(f"Erro ao atualizar oferta: {str(e)}")
        return jsonify({'error': 'Erro interno ao atualizar oferta.'}), 500

@offer_blueprint.route('/list_offers', methods=['GET'])
@login_required_api
def list_offers():
    try:
        # Só lista ofertas do usuário autenticado
        offers = TradeOffer.query.filter_by(partnersteamid=session.get('steam_id')).all()
        result = [
            {
                'id': offer.id,
                'tradeofferid': offer.tradeofferid,
                'partnersteamid': offer.partnersteamid,
                'status': offer.status,
                'expires_at': offer.expires_at.isoformat()
            }
            for offer in offers
        ]
        return jsonify(result), 200

    except Exception as e:
        current_app.logger.error(f"Erro ao listar ofertas: {str(e)}")
        return jsonify({'error': 'Erro interno ao listar ofertas.'}), 500
