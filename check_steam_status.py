import requests

try:
    print('=== VERIFICACAO STATUS STEAM ===')
    
    # Testar Steam API
    response = requests.get('https://api.steampowered.com/ISteamWebAPIUtil/GetServerInfo/v1/', timeout=10)
    print(f'Steam API Status: {response.status_code}')
    
    # Testar Steam Community
    response2 = requests.get('https://steamcommunity.com/', timeout=10)
    print(f'Steam Community Status: {response2.status_code}')
    
    # Testar Steam Store
    response3 = requests.get('https://store.steampowered.com/', timeout=10)
    print(f'Steam Store Status: {response3.status_code}')
    
    if response.status_code == 200 and response2.status_code == 200:
        print('Steam esta ONLINE e funcionando')
    else:
        print('Steam pode estar com PROBLEMAS')
        
except Exception as e:
    print(f'ERRO ao verificar Steam: {e}')
