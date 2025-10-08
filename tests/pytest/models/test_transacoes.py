from datetime import datetime
from models.transacoes import Transacao
import pytest

@pytest.mark.usefixtures("db_session")
class TestTransacao:

    def test_criar_transacao(self, db_session):
        transacao = Transacao(
            steamid="76561198000000000",
            valor=250.0,
            metodo="pix",
            status="pendente"
        )
        db_session.add(transacao)
        db_session.commit()

        resultado = db_session.query(Transacao).first()

        assert resultado is not None
        assert resultado.steamid == "76561198000000000"
        assert resultado.valor == 250.0
        assert resultado.metodo == "pix"
        assert resultado.status == "pendente"
        assert isinstance(resultado.criado_em, datetime)

    def test_repr_transacao(self):
        transacao = Transacao(
            steamid="76561198000000000",
            valor=250.0,
            metodo="pix",
            status="pendente"
        )
        repr_result = repr(transacao)
        assert "<Transacao 76561198000000000 - R$ 250.0 - pendente>" in repr_result
