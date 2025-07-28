from db_config import db


class Saldo(db.Model):
    __tablename__ = 'saldos'

    id = db.Column(db.Integer, primary_key=True)
    steamid = db.Column(db.String(50), unique=True, nullable=False)
    valor = db.Column(db.Float, default=0.0)

    def __repr__(self):
        return f"<Saldo {self.steamid}: R$ {self.valor:.2f}>"
    
    @staticmethod
    def get_saldo_atual(steam_id):
        """
        Obtém o saldo atual de um usuário pelo Steam ID
        """
        saldo = Saldo.query.filter_by(steamid=steam_id).first()
        return saldo.valor if saldo else 0.0
