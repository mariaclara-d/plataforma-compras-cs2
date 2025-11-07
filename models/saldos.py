from db_config import db


class Saldo(db.Model):
    __tablename__ = 'saldos'

    id = db.Column(db.Integer, primary_key=True)
    steamid = db.Column(db.String(50), unique=True, nullable=False, index=True)
    valor = db.Column(db.Numeric(10, 2), default=0.0)

    def __repr__(self):
        return f"<Saldo {self.steamid}: R$ {self.valor:.2f}>"
    
    @staticmethod
    def get_saldo_atual(steam_id):
        """
        Obtém o saldo atual de um usuário pelo Steam ID
        """
        saldo = Saldo.query.filter_by(steamid=steam_id).first()
        return saldo.valor if saldo else 0.0
    
    @staticmethod
    def criar_ou_atualizar_saldo(steam_id, novo_valor):
        """
        Cria ou atualiza o saldo de um usuário
        """
        saldo = Saldo.query.filter_by(steamid=steam_id).first()
        
        if not saldo:
            saldo = Saldo(steamid=steam_id, valor=novo_valor)
            db.session.add(saldo)
        else:
            saldo.valor = novo_valor

        db.session.commit()
        return saldo
    
    @staticmethod
    def adicionar_valor(steam_id, valor_adicional):
        """
        Adiciona um valor ao saldo do usuário
        """

        saldo = Saldo.query.filter_by(steamid=steam_id).first()
        if not saldo:
            saldo = Saldo(steamid=steam_id, valor=valor_adicional)
            db.session.add(saldo)
        else:
            saldo.valor = (saldo.valor or 0) + valor_adicional

        db.session.commit()
        return saldo
    
    def to_dict(self):
        return {
            'id': self.id,
            'steamid': self.steamid,
            'valor': str(self.valor) if self.valor else 0.0
        }