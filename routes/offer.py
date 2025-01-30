from flask import Blueprint
from db_config import db
from app import app
from models import TradeOffer


offer_blueprint = Blueprint('offer', __name__, template_folder="../templates")


@offer_blueprint.route('/create_trade_offer', methods=['POST'])
def create_trade_offer():
    # Exemplo de dados para adicionar uma oferta
    new_offer = TradeOffer(
        tradeofferid="123456789",
        partnersteamid="76561198000000000",
        expires_at="2025-02-01 23:59:59"
    )

    try:
        db.session.add(new_offer)
        db.session.commit()
        
        
        
        
        
        return f"Oferta de troca {new_offer.tradeofferid} criada com sucesso!"
    except Exception as e:
        return f"Erro ao criar oferta de troca: {str(e)}"

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
