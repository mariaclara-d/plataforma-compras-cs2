# README - Preparação para Testes Cypress

## 🔒 SEGURANÇA PARA TESTES PÚBLICOS

### ✅ Arquivos protegidos pelo .gitignore:
- `.env` - Configurações sensíveis 
- `config/steam/steam_guard.json` - Credenciais Steam
- `*_guard.json` - Qualquer arquivo guard
- `instance/` - Banco de dados local

### ⚠️ ANTES DE COMMITAR:

1. **Verificar se dados sensíveis não estão expostos:**
```bash
git status
git diff --cached
```

2. **Usar apenas .env.example:**
```bash
cp .env .env.example  # NUNCA faça isso!
# Em vez disso, edite .env.example manualmente
```

3. **Configurar variáveis no CI/CD:**
```
COMPANY_NAME=TestCompany
STEAM_COMMUNITY_URL=https://steamcommunity.com
```

## 🧪 CONFIGURAÇÃO PARA CYPRESS

### Endpoints de teste recomendados:
- `/api/health` - Health check
- `/api/inventory/test` - Dados mock
- `/api/trade/validate` - Validação de formulários

### Variáveis de ambiente para teste:
```env
FLASK_ENV=testing
DEBUG=False
TESTING=True
WTF_CSRF_ENABLED=False  # Para facilitar testes automatizados
```

### Mock de dados Steam:
- Usar dados fictícios para inventário
- URLs de teste para Steam API
- Credenciais de teste (não reais)

## 🚀 COMANDOS PARA DEPLOY

```bash
# 1. Verificar arquivos sensíveis
git ls-files | grep -E '\.(env|key|json)$'

# 2. Limpar cache
git rm -r --cached .
git add .
git commit -m "Update .gitignore and remove sensitive files"

# 3. Push seguro
git push origin main
```