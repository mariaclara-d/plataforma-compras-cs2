from db_config import db
from datetime import datetime, timezone
from sqlalchemy import event
import logging

logger = logging.getLogger(__name__)

class TradeOffer(db.Model):
    __tablename__ = 'trade_offers'

    id = db.Column(db.Integer, primary_key=True)
    tradeofferid = db.Column(db.String(50), nullable=False, unique=True, index=True)
    partnersteamid = db.Column(db.String(50), nullable=False, index=True)  # Steam ID do parceiro
    status = db.Column(db.String(20), nullable=False, default='pendente', index=True)  # pendente, aceito, recusado, cancelado
    cancelado_por = db.Column(db.String(20), nullable=True)  # "usuario", "site"
    
    # Campos adicionais para melhor rastreamento
    valor_total = db.Column(db.Numeric(10, 2), nullable=True)
    items_count = db.Column(db.Integer, default=0)
    error_message = db.Column(db.Text, nullable=True)  # Para guardar mensagens de erro

    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)

    def __repr__(self):
        return f"<Oferta {self.tradeofferid} - {self.status} - R${self.valor_total}>"
    
    def is_expired(self):
        """Verifica se a oferta expirou"""
        return datetime.now(timezone.utc) > self.expires_at
    
    def can_be_cancelled(self):
        """Verifica se a oferta pode ser cancelada"""
        return self.status in ['pendente'] and not self.is_expired()

# Event listener para logging automático
@event.listens_for(TradeOffer, 'after_insert')
def log_trade_offer_creation(mapper, connection, target):
    logger.info(f"[TRADE_OFFER] Nova oferta criada: {target.tradeofferid} para {target.partnersteamid}")

@event.listens_for(TradeOffer, 'after_update')
def log_trade_offer_update(mapper, connection, target):
    logger.info(f"[TRADE_OFFER] Oferta atualizada: {target.tradeofferid} -> Status: {target.status}")
