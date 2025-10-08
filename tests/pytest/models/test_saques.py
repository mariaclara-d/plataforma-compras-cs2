""" class Saque:
    'saques'

    id = Integer
    steamid = String(50); ForeignKey('saldos.steamid')
    valor = Float
    status = String(20); Default('pendente')
    criado_em = DateTime; Default(datetime.now(timezone.utc))
    atualizado_em = DateTime; Default(datetime.now(timezone.utc)); OnUpdate(datetime.utcnow)
    # Adiciona um método __repr__ para representar o objeto Saque como uma string
    def __repr__(self):
        return f"<Saque {self.steamid}: R$ {self.valor:.2f} - {self.status}>" # Retorna uma string com o steamid, valor e status do saque
"""
from models.saques import Saque


def test_saque_repr():
    # Testa o método __repr__ com um saque pendente
    saque = Saque(steamid='1234567890', valor=100.0, status='pendente')
    assert repr(saque) == "<Saque 1234567890: R$ 100.00 - pendente>"
    # Testa o método __repr__ com um saque pendente
    saque.status = 'aprovado' 
    assert repr(saque) == "<Saque 1234567890: R$ 100.00 - aprovado>"
    # Testa o método __repr__ com um saque aprovado
    saque.status = 'rejeitado'
    assert repr(saque) == "<Saque 1234567890: R$ 100.00 - rejeitado>"
 

