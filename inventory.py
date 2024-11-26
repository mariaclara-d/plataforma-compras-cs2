import os
import requests
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Inicializar a chave da API Steam
steam_api_key_inventory = os.getenv("STEAM_API_KEY_NAO_OFICIAL")

# Função para validar se o tradelink corresponde ao usuário logado
def validate_tradelink(tradelink, user_steam_id):
    try:
        # Extraia o `partner_id` do tradelink
        tradelink_steam_id = tradelink.split("partner=")[1].split("&")[0]
        partner_id = int(tradelink_steam_id)
        calculated_steam_id = str(partner_id + 76561197960265728)
    except (IndexError, ValueError):
        print("Erro: Tradelink está no formato incorreto.")
        return False

    # Remover o prefixo "https://steamcommunity.com/openid/id/" do user_steam_id
    user_steam_id = user_steam_id.replace("https://steamcommunity.com/openid/id/", "")

    # Validar se o Steam ID do tradelink corresponde ao usuário logado
    if calculated_steam_id != user_steam_id:
        print(f"Erro: Tradelink ID ({calculated_steam_id}) não corresponde ao user_steam_id ({user_steam_id}).")
        return False

    print("Tradelink validado com sucesso!")
    return True

# Função para obter o inventário do usuário usando a API da Steam
def get_user_inventory(steam_api_key_inventory, user_steam_id):
    # Remover o prefixo do Steam ID se necessário
    if user_steam_id.startswith("https://steamcommunity.com/openid/id/"):
        user_steam_id = user_steam_id.replace("https://steamcommunity.com/openid/id/", "")

    # URL para buscar o inventário
    url = f"https://www.steamwebapi.com/steam/api/inventory?key={steam_api_key_inventory}&steam_id={user_steam_id}"
    response = requests.get(url)

    if response.ok:
        try:
            data = response.json()
            inventory = []
            for item in data:  # Iterar pelos itens retornados
                inventory_item = {
                    "name": item.get("marketname", "N/A"),
                    "assetid": item.get("assetid"),
                    "tradable": item.get("tradable", False),
                    "image_url": item.get("image", ""),
                    "rarity": item.get("rarity", "N/A"),
                    "inspect_link": item.get("inspectlink", "")
                }
                inventory.append(inventory_item)
            return inventory
        except ValueError as e:
            print(f"Erro ao processar a resposta JSON: {str(e)}")
            return []
    else:
        print(f"Erro ao buscar inventário para o ID {user_steam_id}: {response.status_code}")
        return []

# Função principal para retornar o inventário validado
def fetch_inventory(tradelink, user_steam_id):
    # Validar o tradelink
    if not validate_tradelink(tradelink, user_steam_id):
        return {"error": "Tradelink não corresponde ao usuário logado."}, 400

    # Obter o inventário do usuário
    inventory = get_user_inventory(steam_api_key_inventory, user_steam_id)
    return {
        "steam_id": user_steam_id,
        "tradelink": tradelink,
        "inventory": inventory
    }
