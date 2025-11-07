from db_config import db


class InformacoesPagamento(db.Model):
    __tablename__ = 'informacoes_pagamento'

    id = db.Column(db.Integer, primary_key=True)
    steamid = db.Column(db.String(50), unique=True, nullable=False)
    tradelink = db.Column(db.String(255), nullable=False)
    metodo_pagamento = db.Column(db.String(50), nullable=False)  # pix, transferencia, cripto
    chave_pix = db.Column(db.String(255), nullable=True)
    banco = db.Column(db.String(255), nullable=True)
    agencia = db.Column(db.String(50), nullable=True)
    conta = db.Column(db.String(50), nullable=True)
    tipo_conta = db.Column(db.String(50), nullable=True)
    carteira = db.Column(db.String(255), nullable=True)  # cripto

    def __repr__(self):
        return f"<Pagamento {self.steamid} via {self.metodo_pagamento}>"
