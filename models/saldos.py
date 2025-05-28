from db_config import db


class Saldo(db.Model):
    __tablename__ = 'saldos'

    id = db.Column(db.Integer, primary_key=True)
    steamid = db.Column(db.String(50), unique=True, nullable=False)
    valor = db.Column(db.Float, default=0.0)

    def __repr__(self):
        return f"<Saldo {self.steamid}: R$ {self.valor:.2f}>"
