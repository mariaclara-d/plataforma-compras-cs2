# -*- coding: utf-8 -*-
import re

# Ler arquivo
with open('routes/trade.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Correções específicas
fixes = [
    # Garantir conversão para int
    (r'wait_time = tentativa_atual \* (\d+)', r'wait_time = int(tentativa_atual) * \1'),
    (r'wait_time = (\d+) \+ \(tentativa_atual \* (\d+)\)', r'wait_time = \1 + (int(tentativa_atual) * \2)'),
    # Remover emojis restantes
    ('🚨', '[ALERT]'),
    ('❌', '[ERROR]'),
    ('✅', '[OK]'),
    ('🔄', '[RETRY]'),
    ('⚠️', '[WARN]'),
    ('🔐', '[AUTH]'),
    ('💾', '[SAVE]'),
    ('📤', '[SEND]'),
    ('🕐', '[CLOCK]'),
    ('⏳', '[HOURGLASS]'),
    ('⏱️', '[TIMER]'),
    ('🌐', '[GLOBE]'),
    ('🔍', '[SEARCH]'),
    ('🔒', '[LOCK]')
]

# Aplicar correções
for old, new in fixes:
    content = re.sub(old, new, content)

# Salvar arquivo corrigido
with open('routes/trade.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('✅ Arquivo routes/trade.py corrigido!')
