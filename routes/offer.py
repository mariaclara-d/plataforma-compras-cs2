from flask import Blueprint, request, jsonify, current_app
from db_config import db
from models import TradeOffer
from datetime import datetime, timedelta, timezone

offer_blueprint = Blueprint('offer', __name__, template_folder="../templates")

@offer_blueprint.route('/create_trade_offer', methods=['POST'])
def create_trade_offer():
    try:
        # Recebendo os dados do corpo da requisição
        data = request.json
        tradeofferid = data.get('tradeofferid')
        partnersteamid = data.get('partnersteamid')

        # Define o tempo de expiração (10 minutos a partir de agora)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
        
        # Verificando se todos os campos foram fornecidos
        if not tradeofferid or not partnersteamid:
            return jsonify({'error': 'Todos os campos (tradeofferid, partnersteamid) são obrigatórios'}), 400

        # Criando uma nova entrada na tabela TradeOffer
        new_offer = TradeOffer(
            tradeofferid=tradeofferid,
            partnersteamid=partnersteamid,
            expires_at=expires_at
        )
        db.session.add(new_offer)
        db.session.commit()

        return jsonify({'message': f"Oferta de troca {new_offer.tradeofferid} criada com sucesso!"}), 201
    except Exception as e:
        return jsonify({'error': f"Erro ao criar oferta de troca: {str(e)}"}), 500


@offer_blueprint.route('/update_trade_offer/<int:offer_id>', methods=['PUT'])
def update_trade_offer(offer_id):
    try:
        offer = TradeOffer.query.get(offer_id)
        if offer:
            offer.status = "aceito"  # Exemplo: alterando o status para 'aceito'
            db.session.commit()
            return f"Status da oferta {offer.tradeofferid} atualizado para {offer.status}!"
        else:
            return f"Oferta de ID {offer_id} não encontrada."
    except Exception as e:
        return f"Erro ao atualizar oferta: {str(e)}"
