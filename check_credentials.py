import os
from dotenv import load_dotenv
load_dotenv()

print('=== VERIFICACAO DE CREDENCIAIS ===')
print(f'STEAM_USERNAME: {os.getenv("STEAM_USERNAME")}')
print(f'STEAM_PASSWORD: {"***" if os.getenv("STEAM_PASSWORD") else "NONE"}')
print(f'STEAM_ID: {os.getenv("STEAM_ID")}')

# Verificar se Steam Guard esta ativo
import json
from pathlib import Path
try:
    config_file = Path('config/steam/steam_guard.json')
    with open(config_file, 'r') as f:
        config = json.load(f)
    print(f'Steam Guard Secrets: OK ({len(config["shared_secret"])} chars)')
except Exception as e:
    print(f'Steam Guard Secrets: ERRO - {e}')
