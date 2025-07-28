#!/bin/bash
echo "Aplicando correção urgente..."

# Backup do arquivo original
docker-compose exec web cp /app/services/aiosteampy_service.py /app/services/aiosteampy_service.py.backup

# Aplicar correção direta
docker-compose exec web python3 -c "
import re

# Ler arquivo atual
with open('/app/services/aiosteampy_service.py', 'r') as f:
    content = f.read()

# Encontrar a linha de carregamento do inventário
old_line = '    user_inventory = await client.get_user_inventory('
new_code = '''    # TESTE CRÍTICO PRIMEIRO
    print(f\"🔍 TESTE: Verificando acesso direto ao inventário...\")
    import aiohttp
    
    test_url = f\"https://steamcommunity.com/inventory/{partner_steamid64}/730/2\"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(test_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    print(f\"✅ TESTE: Inventário acessível via URL direta\")
                elif response.status == 400:
                    print(f\"❌ TESTE: ERRO 400 - Inventário inacessível\")
                    raise RuntimeError(\"❌ ERRO 400: Inventário não existe ou está privado\")
                else:
                    print(f\"❌ TESTE: Status {response.status}\")
                    raise RuntimeError(f\"❌ Erro {response.status} ao acessar inventário\")
    except Exception as e:
        print(f\"❌ TESTE FALHOU: {e}\")
        raise RuntimeError(f\"❌ Pré-validação falhou: {e}\")
    
    # Agora tentar aiosteampy
    user_inventory = await client.get_user_inventory('''

# Substituir
if old_line in content:
    content = content.replace(old_line, new_code)
    print('✅ Correção aplicada')
else:
    print('❌ Linha não encontrada')

# Salvar arquivo
with open('/app/services/aiosteampy_service.py', 'w') as f:
    f.write(content)

print('🔄 Arquivo atualizado')
"

echo "✅ Correção aplicada! Testando..."
