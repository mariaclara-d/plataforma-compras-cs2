from db_config import db
from datetime import datetime

class Saque(db.Model):
    __tablename__ = 'saques'

    id = db.Column(db.Integer, primary_key=True)
    steamid = db.Column(db.String(50), nullable=False)
    valor = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pendente')  # pendente, aprovado, recusado, pago
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Saque {self.steamid}: R$ {self.valor:.2f} - {self.status}>"
