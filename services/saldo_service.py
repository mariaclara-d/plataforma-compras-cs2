
from models.saldos import Saldo
from decimal import Decimal

def calcular_saldo_usuario(steamid):
    """
    Calcula o saldo disponível do usuário.
    Usa o método do modelo Saldo que já implementa toda lógica corretamente.
    """

    # Usar método do modelo (que já está correto)
    saldo_atual = Saldo.get_saldo_atual(steamid)

    # Garantir que retorna Decimal para compatibilidade
    return saldo_atual if saldo_atual is not None else Decimal('0.00')