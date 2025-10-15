from db_config import db
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship


class Skin(db.Model):
    __tablename__ = 'skins'

    id = db.Column(db.Integer, primary_key=True)
    tradeofferid = db.Column(db.String(50), db.ForeignKey('trade_offers.tradeofferid'), nullable=False)  # Referência à oferta
    nome = db.Column(db.String(100), nullable=False)
    preco = db.Column(db.Numeric(10, 2), nullable=True)
    valor_liquido = db.Column(db.Numeric(10, 2), nullable=True)  # NOVO: valor com comissão
    raridade = db.Column(db.String(50), nullable=True)
    descricao = db.Column(db.Text, nullable=True)
    assetid = db.Column(db.String(50), nullable=False)

    trade_offer = db.relationship('TradeOffer', backref='skins')

    def __repr__(self):
        return f"<Skin {self.nome} - R$ {self.preco} (R$ {self.valor_liquido} líquido)>"
    

    def to_dict(self):
        return {
            'id': self.id,
            'tradeofferid': self.tradeofferid,
            'nome': self.nome,
            'preco': str(self.preco) if self.preco is not None else None,
            'valor_liquido': str(self.valor_liquido) if self.valor_liquido is not None else None,
            'raridade': self.raridade,
            'descricao': self.descricao,
            'assetid': self.assetid
        }
