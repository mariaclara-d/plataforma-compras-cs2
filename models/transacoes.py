from db_config import db

from datetime import datetime

class Transacao(db.Model):
    __tablename__ = 'transacoes'

    id = db.Column(db.Integer, primary_key=True)
    steamid = db.Column(db.String(50), nullable=False)
    valor = db.Column(db.Float, nullable=False)
    metodo = db.Column(db.String(20), nullable=False)  # pix, banco, cripto
    status = db.Column(db.String(20), default='pendente')  # pendente, pago, cancelado
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Transacao {self.steamid} - R$ {self.valor} - {self.status}>"
