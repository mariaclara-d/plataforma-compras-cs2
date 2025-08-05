import base64
import json
from pathlib import Path

try:
    config_file = Path('config/steam/steam_guard.json')
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    # Testar decodificacao Base32
    shared = config['shared_secret']
    identity = config['identity_secret']
    
    print('=== VERIFICACAO STEAM GUARD ===')
    print(f'Shared Secret: {len(shared)} chars')
    print(f'Identity Secret: {len(identity)} chars')
    
    # Adicionar padding se necessario
    for name, secret in [('shared_secret', shared), ('identity_secret', identity)]:
        missing_padding = len(secret) % 8
        if missing_padding:
            secret += '=' * (8 - missing_padding)
        
        try:
            decoded = base64.b32decode(secret)
            status = 'VALIDO' if len(decoded) == 20 else 'INVALIDO'
            print(f'{name}: {len(decoded)} bytes - {status}')
        except Exception as e:
            print(f'{name}: ERRO na decodificacao - {e}')
        
except Exception as e:
    print(f'ERRO ao verificar secrets: {e}')
