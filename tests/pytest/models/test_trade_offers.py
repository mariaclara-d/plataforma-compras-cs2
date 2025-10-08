from datetime import datetime, timedelta, timezone
from models.trade_offers import TradeOffer
import pytest

@pytest.mark.usefixtures("db_session")
class TestTradeOffer:
 # ----------------------------- Criação e representação -----------------------------
    def test_criar_trade_offer(self, db_session):
        # - Definir data de expiração
        # - Criar objeto TradeOffer
        # - Verificar se o objeto foi criado corretamente
        # - Adicionar/comitar no banco
        # - Verificar no banco
        # - Asserts
        pass
    def test_repr_trade_offer(self):
        # - Criar objeto TradeOffer
        # - Verificar se a representação (__repr__) é a esperada
        # - Assert
        pass

 # ----------------------------- Status básico -----------------------------
    def test_status_trade_offer(self):
        # - Criar objeto TradeOffer
        # - Verificar status inicial
        # - Assert
        pass

 # ----------------------------- Expiração -----------------------------
    def test_expire_trade_offer(self):
        # - Criar objeto com data de expiração passada
        # - Verificar se o status é 'expired'
        # - Assert
        pass

 # ----------------------------- Ações do usuário -----------------------------
    def test_accept_trade_offer(self):
        # - Criar objeto
        # - Simular aceitação
        # - Verificar se o status é 'accepted'
        # - Assert
        pass

    def test_reject_trade_offer(self):
        # - Criar objeto
        # - Simular rejeição
        # - Verificar se o status é 'rejected'
        # - Assert
        pass

    def test_cancel_trade_offer(self):
        # - Criar objeto
        # - Simular cancelamento
        # - Verificar se o status é 'canceled'
        # - Assert
        pass

 # ----------------------------- Expiração automática -----------------------------
    def test_auto_expire_trade_offer(self):
        # - Criar objeto com data de expiração futura
        # - Esperar até a expiração
        # - Verificar status 'expired'
        # - Assert
        pass

    def test_auto_expire_trade_offer_past_date(self):
        # - Criar objeto com data de expiração passada
        # - Esperar até a expiração
        # - Verificar status 'expired'
        # - Assert
        pass

    def test_auto_expire_trade_offer_future_date(self):
        # - Criar objeto com data de expiração futura
        # - Esperar até a expiração
        # - Verificar status 'expired'
        # - Assert
        pass

 # ----------------------------- Expiração futura combinada com status -----------------------------
    def test_auto_expire_trade_offer_future_date_pending_status(self):
        # - Criar objeto com expiração futura e status 'pending'
        # - Verificar expiração
        # - Assert
        pass

    def test_auto_expire_trade_offer_future_date_accepted_status(self):
        # - Criar objeto com expiração futura e status 'accepted'
        # - Verificar expiração
        # - Assert
        pass

    def test_auto_expire_trade_offer_future_date_rejected_status(self):
        # - Criar objeto com expiração futura e status 'rejected'
        # - Verificar expiração
        # - Assert
        pass

    def test_auto_expire_trade_offer_future_date_canceled_status(self):
        # - Criar objeto com expiração futura e status 'canceled'
        # - Verificar expiração
        # - Assert
        pass
