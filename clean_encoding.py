# -*- coding: utf-8 -*-
import re

# Ler arquivo
with open('services/aiosteampy_service.py', 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Correções específicas de encoding
fixes = [
    # Corrigir palavras corrompidas
    ('Inst ncias', 'Instancias'),
    ('Fun o', 'Funcao'),
    ('Compat vel', 'Compativel'),
    ('c digo', 'codigo'),
    ('implementa o', 'implementacao'),
    ('n o', 'nao'),
    ('inválido', 'invalido'),
    ('não', 'nao'),
    ('válido', 'valido'),
    ('obrigatório', 'obrigatorio'),
    ('obrigatória', 'obrigatoria'),
    
    # Remover caracteres não-ASCII restantes
    (r'[^\x00-\x7F]+', ' ')  # Substituir qualquer não-ASCII por espaço
]

# Aplicar correções
for old, new in fixes:
    if old.startswith('r\''):
        # Regex
        content = re.sub(old, new, content)
    else:
        # String literal
        content = content.replace(old, new)

# Limpar espaços extras
content = re.sub(r'  +', ' ', content)
content = re.sub(r'\n +\n', '\n\n', content)

# Salvar arquivo limpo
with open('services/aiosteampy_service.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('[OK] Caracteres de encoding corrigidos!')
