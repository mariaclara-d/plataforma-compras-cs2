from db_config import db

from datetime import datetime, timezone

class TradeOffer(db.Model):
    __tablename__ = 'trade_offers'

    id = db.Column(db.Integer, primary_key=True)
    tradeofferid = db.Column(db.String(50), nullable=False)
    partnersteamid = db.Column(db.String(50), nullable=False)  # Steam ID do parceiro
    status = db.Column(db.String(20), nullable=False, default='pendente')  # pendente, aceito, recusado, cancelado
    cancelado_por = db.Column(db.String(20), nullable=True)  # "usuario", "site"

    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)

    def __repr__(self):
        return f"<Oferta {self.tradeofferid} - {self.status}>"
