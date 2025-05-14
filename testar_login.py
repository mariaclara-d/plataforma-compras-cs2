import asyncio
from aiosteampy.client import SteamClient
import json

# Carrega o arquivo steam_guard.json
with open("steam_guard.json", "r") as f:
    steam_guard = json.load(f)

username = steam_guard["account_name"]
password = steam_guard["password"]
shared_secret = steam_guard["shared_secret"]
identity_secret = steam_guard["identity_secret"]
steam_id = steam_guard["steam_id"]

async def main():
    print("🔐 Tentando logar com aiosteampy...")
    try:
        # Agora com steam_id
        client = SteamClient(
            username=username,
            password=password, 
            shared_secret=shared_secret,
            identity_secret=identity_secret,
            steam_id=steam_id
        )

        await client.login()
        print("Login bem-sucedido com aiosteampy!")
        await client.logout()

    except Exception as e:
        print(f"Erro no login: {e}")

if __name__ == "__main__":
    asyncio.run(main())

