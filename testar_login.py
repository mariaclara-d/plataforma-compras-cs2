from steampy.client import SteamClient
from steampy.client import SteamClient
from dotenv import load_dotenv
import os

# Carregar .env
load_dotenv()

print("🔐 Tentando logar na conta bot...")

try:
    api_key = os.getenv("STEAM_API_KEY")
    if not api_key:
        raise Exception("❌ API Key não encontrada no .env")

    client = SteamClient(api_key)
    client.login(username="montanhafetida", password="Tobias132", steam_guard="steam_guard.json")

    print("✅ Login bem-sucedido!")

except Exception as e:
    print(f"❌ Erro ao logar: {e}")

