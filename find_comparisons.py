import re

# Ler o arquivo
with open('services/aiosteampy_service.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Procurar por comparações suspeitas
problematic_patterns = [
    r'(\w+)\s*<\s*(\w+)',  # var < var
    r'(\w+)\s*>\s*(\w+)',  # var > var
    r'(\w+)\s*<=\s*(\w+)', # var <= var
    r'(\w+)\s*>=\s*(\w+)', # var >= var
    r'(\w+)\s*==\s*(\w+)', # var == var
    r'(\w+)\s*!=\s*(\w+)'  # var != var
]

print('=== COMPARAÇÕES ENCONTRADAS ===')
for i, line in enumerate(lines, 1):
    for pattern in problematic_patterns:
        matches = re.findall(pattern, line.strip())
        if matches and not line.strip().startswith('#'):
            print(f'Linha {i}: {line.strip()}')
            for match in matches:
                print(f'  -> Comparação: {match[0]} vs {match[1]}')
            print()
