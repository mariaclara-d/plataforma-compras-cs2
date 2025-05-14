import asyncio
from aiosteampy.client import SteamClient
from aiosteampy.constants import AppContext
import json
import re

# Carrega steam_guard.json
with open("steam_guard.json", "r") as f:
    steam_guard = json.load(f)

username = steam_guard["account_name"]
password = steam_guard["password"]
shared_secret = steam_guard["shared_secret"]
identity_secret = steam_guard["identity_secret"]
steam_id = steam_guard["steam_id"]

tradelink = "https://steamcommunity.com/tradeoffer/new/?partner=1102819994&token=IwADD8Gg"
item_assetid = "42695553185"

def tradelink_para_steamid64(tradelink: str) -> str:
    match = re.search(r"partner=(\d+)", tradelink)
    if not match:
        raise ValueError("Tradelink inválido")
    steamid32 = int(match.group(1))
    return str(steamid32 + 76561197960265728)

async def main():
    client = SteamClient(
        username=username,
        password=password,
        shared_secret=shared_secret,
        identity_secret=identity_secret,
        steam_id=steam_id
    )

    try:
        print("🔐 Logando com aiosteampy...")
        await client.login()
        print("✅ Login feito.")

        partner_steamid64 = tradelink_para_steamid64(tradelink)

        print("🎒 Buscando item do inventário do parceiro...")
        item = await client.get_user_inventory_item(
            steam_id=partner_steamid64,
            app_context=AppContext.CS2,  # << Aqui usamos CS como app_id=730, context_id="2"
            obj=int(item_assetid)
        )

        if not item:
            print("❌ Item não encontrado no inventário do parceiro.")
            return

        print(f"📦 Item encontrado: {item}")

        print("🚀 Enviando oferta de troca...")
        tradeoffer_id = await client.make_trade_offer(
            obj=tradelink,
            to_give=[],
            to_receive=[item],
            message="Oferta de teste com aiosteampy!"
        )

        print(f"🎉 Oferta enviada com sucesso! ID: {tradeoffer_id}")

    except Exception as e:
        print("❌ Erro:", e)

    finally:
        await client.logout()

if __name__ == "__main__":
    asyncio.run(main())




