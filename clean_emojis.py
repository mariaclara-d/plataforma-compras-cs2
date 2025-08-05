# -*- coding: utf-8 -*-
import re

# Ler arquivo
with open('services/aiosteampy_service.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Remover TODOS os caracteres não-ASCII (emojis)
# Manter apenas caracteres ASCII seguros
content_clean = ""
for char in content:
    if ord(char) < 128 or char in ['\n', '\r', '\t']:
        content_clean += char
    else:
        # Substituir emoji por espaço
        content_clean += " "

# Limpar espaços duplos
content_clean = re.sub(r'  +', ' ', content_clean)

# Correções específicas de logs
fixes = [
    (r'logger\.info\(f" ', r'logger.info(f"[AUTH] '),
    (r'logger\.warning\(f" ', r'logger.warning(f"[WARN] '),
    (r'logger\.error\(f" ', r'logger.error(f"[ERROR] '),
    (r'logger\.info\(" ', r'logger.info("[INFO] '),
    (r'logger\.warning\(" ', r'logger.warning("[WARN] '),
    (r'logger\.error\(" ', r'logger.error("[ERROR] ')
]

# Aplicar correções
for old, new in fixes:
    content_clean = re.sub(old, new, content_clean)

# Salvar arquivo limpo
with open('services/aiosteampy_service.py', 'w', encoding='utf-8') as f:
    f.write(content_clean)

print('[OK] Emojis removidos do aiosteampy_service.py!')
