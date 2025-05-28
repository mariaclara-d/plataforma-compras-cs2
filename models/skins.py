from db_config import db


class Skin(db.Model):
    __tablename__ = 'skins'

    id = db.Column(db.Integer, primary_key=True)
    tradeofferid = db.Column(db.String(50), nullable=False)  # Referência à oferta
    nome = db.Column(db.String(100), nullable=False)
    preco = db.Column(db.Float, nullable=True)
    valor_liquido = db.Column(db.Float, nullable=True)  # NOVO: valor com comissão
    raridade = db.Column(db.String(50), nullable=True)
    descricao = db.Column(db.Text, nullable=True)
    assetid = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return f"<Skin {self.nome} - R$ {self.preco} (R$ {self.valor_liquido} líquido)>"
