#  Deploy - Scripts e Configurações

# 🚀 Deploy Heroku - CS2 Marketplace

## ✅ Pré-requisitos

1. **Heroku CLI instalado**: https://devcenter.heroku.com/articles/heroku-cli
2. **Git configurado** e código commitado
3. **Steam API Key**: https://steamcommunity.com/dev/apikey

## 🚀 Deploy Automático

Execute o script PowerShell:

```powershell
.\deploy\deploy_heroku.ps1
```

O script irá:
- ✅ Verificar dependências
- ✅ Criar aplicação Heroku
- ✅ Configurar PostgreSQL
- ✅ Configurar variáveis básicas
- ✅ Fazer deploy do código
- ✅ Inicializar banco de dados

## 🔧 Deploy Manual

### 1. Criar aplicação
```bash
heroku create sua-app-cs2
```

### 2. Adicionar PostgreSQL
```bash
heroku addons:create heroku-postgresql:mini
```

### 3. Configurar variáveis essenciais
```bash
heroku config:set FLASK_ENV=production
heroku config:set SECRET_KEY=sua_chave_secreta_forte
heroku config:set STEAM_API_KEY=sua_steam_api_key
heroku config:set SITE_URL=https://sua-app-cs2.herokuapp.com
```

### 4. Deploy
```bash
git push heroku main
```

### 5. Inicializar banco
```bash
heroku run python -c "from app import create_app; from db_config import db; app = create_app(); app.app_context().push(); db.create_all()"
```

## ⚙️ Configurações Avançadas

### Variáveis Opcionais
Consulte `.env.heroku` para todas as configurações disponíveis.

### Comandos Úteis
```bash
# Ver logs em tempo real
heroku logs --tail

# Verificar status
heroku ps

# Acessar console
heroku run python

# Reiniciar aplicação
heroku restart
```

## 🔒 Segurança

- ✅ Logs sensíveis removidos do Git
- ✅ Credenciais em variáveis de ambiente
- ✅ CSRF protection ativo
- ✅ Headers de segurança configurados

## 🌐 Acesso

Após deploy: **https://sua-app.herokuapp.com**

## 📞 Suporte

Em caso de problemas:
1. Verificar logs: `heroku logs --tail`
2. Verificar configurações: `heroku config`
3. Verificar status: `heroku ps`

##  Arquivos Principais

###  Scripts de Deploy
- **`deploy_heroku.ps1`** - Script automatizado para Windows/PowerShell
- **`deploy_heroku.sh`** - Script automatizado para Linux/Mac
- **`CHECKLIST_DEPLOY.md`** - Guia completo passo-a-passo

##  Deploy Rápido

### Windows:
```powershell
.\deploy\deploy_heroku.ps1
```

### Linux/Mac:
```bash
chmod +x deploy/deploy_heroku.sh
./deploy/deploy_heroku.sh
```

##  Checklist Completo

Siga o arquivo `CHECKLIST_DEPLOY.md` para um deploy detalhado com:
-  Pré-requisitos
-  Configuração Heroku
-  Configuração de domínio
-  Testes finais
-  Planos B para problemas

## ⏱ Tempo Estimado
- **Deploy básico:** 45 minutos
- **Deploy completo:** 4-6 horas
- **Propagação DNS:** 2-48 horas

##  Resultado Esperado
- Site funcionando em `https://sua-app.herokuapp.com`
- Admin acessível em `https://sua-app.herokuapp.com/admin/login`
- Domínio custom configurado (se aplicável)
