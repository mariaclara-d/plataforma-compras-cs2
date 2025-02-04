from app import db

class TradeOffer(db.Model):
    __tablename__ = 'trade_offers'

    id = db.Column(db.Integer, primary_key=True)
    tradeofferid = db.Column(db.String(50), nullable=False)
    partnersteamid = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), default='pendente')  # Valores possíveis: pendente, aceito, recusado, cancelado
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)

