"""
🚨 PROBLEMA CRÍTICO: CREDENCIAIS STEAM GUARD EXPIRADAS

==== DIAGNOSTICO ====
❌ KeyError: 'client_id' - Steam REJEITOU as credenciais
❌ KeyError: 'access_token' - Steam não conseguiu autenticar

==== SOLUÇÃO ====
1. As credenciais Steam Guard estão EXPIRADAS ou INCORRETAS
2. Você precisa GERAR NOVAS credenciais Steam Guard

==== COMO GERAR NOVAS CREDENCIAIS ====

OPÇÃO 1 - Steam Desktop Authenticator:
1. Baixe Steam Desktop Authenticator
2. Configure com sua conta Steam
3. Exporte os secrets (shared_secret e identity_secret)
4. Atualize config/steam/steam_guard.json

OPÇÃO 2 - Usar conta Steam diferente:
1. Crie uma conta Steam nova só para bot
2. Configure Steam Guard nela
3. Gere as credenciais
4. Use essa conta para trades

OPÇÃO 3 - Usar WinAuth ou similar:
1. Configure WinAuth com sua conta Steam
2. Exporte os dados do Steam Guard
3. Extraia shared_secret e identity_secret

==== ARQUIVO A ATUALIZAR ====
config/steam/steam_guard.json:
{
    "account_name": "seu_usuario",
    "password": "sua_senha",
    "shared_secret": "NOVO_SHARED_SECRET_AQUI",
    "identity_secret": "NOVO_IDENTITY_SECRET_AQUI", 
    "steam_id": SEU_STEAM_ID_64
}

==== DEPOIS DE ATUALIZAR ====
Execute: python verificar_steam.py

SEM CREDENCIAIS VÁLIDAS = SEM OFERTAS REAIS!
"""
