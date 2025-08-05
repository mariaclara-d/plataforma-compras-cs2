import pyotp
import json
from pathlib import Path

try:
    config_file = Path('config/steam/steam_guard.json')
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    shared_secret = config['shared_secret']
    
    # Adicionar padding se necessario
    missing_padding = len(shared_secret) % 8
    if missing_padding:
        shared_secret += '=' * (8 - missing_padding)
    
    # Gerar codigo atual
    totp = pyotp.TOTP(shared_secret)
    current_code = totp.now()
    
    print('=== CODIGO 2FA STEAM ===')
    print(f'Codigo 2FA atual: {current_code}')
    print('Use este codigo se for solicitado manualmente.')
    
except Exception as e:
    print(f'Erro ao gerar codigo 2FA: {e}')
    print('Instale pyotp: pip install pyotp')
