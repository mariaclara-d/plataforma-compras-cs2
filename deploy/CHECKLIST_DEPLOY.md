# 📋 CHECKLIST DEPLOY AMANHÃ - PLATAFORMA CS2

## ⏰ **CRONOGRAMA DETALHADO (4-6 horas)**

### 🌅 **MANHÃ - PREPARAÇÃO (1-2h)**

#### ✅ **PRÉ-REQUISITOS (30 min)**
- [ ] **Instalar Heroku CLI** - https://devcenter.heroku.com/articles/heroku-cli
- [ ] **Verificar Git configurado** - `git status`
- [ ] **Testar containers locais** - `docker-compose up -d`
- [ ] **Testar admin local** - http://localhost:5000/admin/login (admin/admin123)
- [ ] **Gerar chaves novas**:
  - [ ] SECRET_KEY: `python -c "import secrets; print(secrets.token_hex(32))"`
  - [ ] Criar nova conta Steam para bot (se necessário)
  - [ ] Obter nova Steam API Key

#### 🚀 **DEPLOY BÁSICO (45 min)**
- [ ] **Executar script deploy** - `.\deploy_heroku.ps1`
- [ ] **Definir nome da app** - ex: `plataforma-cs2-2025`
- [ ] **Aguardar deploy** - ~10-15 min
- [ ] **Verificar aplicação online** - https://sua-app.herokuapp.com
- [ ] **Testar admin online** - https://sua-app.herokuapp.com/admin/login

#### ⚙️ **CONFIGURAÇÃO ADICIONAL (30 min)**
- [ ] **Configurar Steam no Heroku**:
  ```bash
  heroku config:set STEAM_API_KEY=sua_nova_chave --app sua-app
  heroku config:set STEAM_RETURN_URL=https://sua-app.herokuapp.com/complete_steam_login --app sua-app
  heroku config:set STEAM_REALM=https://sua-app.herokuapp.com --app sua-app
  ```
- [ ] **Verificar logs** - `heroku logs --tail --app sua-app`
- [ ] **Testar funcionalidades básicas**

### 🌄 **TARDE - FINALIZAÇÃO (2h)**

#### 🌐 **CONFIGURAÇÃO DOMÍNIO (30 min)**
- [ ] **No GoDaddy**:
  - [ ] Acessar DNS Management
  - [ ] Criar CNAME: `www` → `sua-app.herokuapp.com`
  - [ ] Criar A Record: `@` → IP do Heroku (ou usar CNAME)
- [ ] **No Heroku**:
  ```bash
  heroku domains:add www.seudominio.com --app sua-app
  heroku domains:add seudominio.com --app sua-app
  ```
- [ ] **Aguardar propagação** (15 min - 48h)

#### 🧪 **TESTES FINAIS (30 min)**
- [ ] **Testar no domínio Heroku** (.herokuapp.com)
- [ ] **Testar páginas principais**:
  - [ ] Homepage
  - [ ] Login admin
  - [ ] Dashboard admin
  - [ ] Página de saques
- [ ] **Verificar logs de erro** - `heroku logs --app sua-app`
- [ ] **Testar responsividade** (mobile/desktop)

#### 📊 **MONITORAMENTO (30 min)**
- [ ] **Configurar alertas Heroku**
- [ ] **Verificar métricas**
- [ ] **Documentar URLs finais**
- [ ] **Backup configuração**

## 🚨 **PLANOS B - Se algo der errado**

### **Se Steam API falhar:**
- [ ] Desabilitar integração Steam temporariamente
- [ ] Deploy sem funcionalidades Steam
- [ ] Configurar na versão 1.1

### **Se domínio não propagar:**
- [ ] Usar subdomínio Heroku temporariamente
- [ ] Configurar domínio depois
- [ ] Informar usuários sobre URL temporária

### **Se deploy falhar:**
- [ ] Verificar logs: `heroku logs --tail`
- [ ] Revisar Procfile e requirements.txt
- [ ] Deploy incremental (sem novas features)

## 📱 **URLs IMPORTANTES**

### **Após Deploy:**
- 🌐 **Site:** https://sua-app.herokuapp.com
- 🔑 **Admin:** https://sua-app.herokuapp.com/admin/login
- 📊 **Heroku Dashboard:** https://dashboard.heroku.com/apps/sua-app
- 📋 **Logs:** `heroku logs --tail --app sua-app`

### **GoDaddy:**
- 🌐 **DNS Management:** https://dcc.godaddy.com/control/dns

## ⚡ **COMANDOS RÁPIDOS**

```bash
# Verificar status
heroku ps --app sua-app

# Ver configurações
heroku config --app sua-app

# Restart aplicação
heroku restart --app sua-app

# Executar comando
heroku run python --app sua-app

# Logs em tempo real
heroku logs --tail --app sua-app
```

## 🎯 **CRITÉRIOS DE SUCESSO**

### **Mínimo (MVP):**
- [ ] Site online e acessível
- [ ] Admin funcionando
- [ ] Páginas principais carregando
- [ ] Sem erros críticos

### **Ideal:**
- [ ] Domínio configurado
- [ ] Steam funcionando
- [ ] Todas as funcionalidades testadas
- [ ] Monitoramento ativo

---

**⏱️ TEMPO TOTAL: 4-6 horas**
**✅ VIABILIDADE: ALTA**
**🚀 STATUS: PRONTO PARA DEPLOY**
