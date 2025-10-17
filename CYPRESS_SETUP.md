# 🔐 CYPRESS SECURITY TESTING SETUP

## 📋 **PRÉ-REQUISITOS PARA TESTES DE SEGURANÇA**

### 1. **Instalar Node.js e Cypress**
```bash
# Verificar se Node.js está instalado
node --version
npm --version

# Instalar Cypress
npm install --save-dev cypress
```

### 2. **Configurar Ambiente de Teste**
```bash
# Instalar dependências
npm install

# Inicializar Cypress
npx cypress open
```

## � **EXECUTANDO TESTES DE SEGURANÇA DE PAGAMENTO**

### **Passo 1: Iniciar Aplicação**
```bash
# Terminal 1: Ativar ambiente e iniciar Flask
.\.venv\Scripts\Activate.ps1
python app.py
```

### **Passo 2: Executar Testes de Segurança**
```bash
# Terminal 2: Executar testes específicos de segurança de pagamento
npx cypress run --spec "cypress/e2e/payment-security.cy.js"

# Ou interface gráfica
npx cypress open
```

## 🎯 **TESTES DE SEGURANÇA IMPLEMENTADOS**

### ✅ **Proteção contra Manipulação de Pagamento:**
- **PIX Key Manipulation**: Impede alteração de chave PIX via interceptação
- **SQL Injection**: Testa injeção em dados de pagamento
- **XSS Prevention**: Verifica escape de dados maliciosos
- **Parameter Tampering**: Confirma validação server-side

### ✅ **Proteção de Saque (Withdrawal):**
- **Cross-User Withdrawal**: Impede saque de conta alheia
- **Trade Hold Protection**: Verifica sistema de proteção de 7 dias
- **Balance Validation**: Confirma verificação de saldo disponível
- **Negative Amount**: Testa valores negativos e inválidos

### ✅ **Autenticação e Autorização:**
- **CSRF Protection**: Verifica tokens CSRF obrigatórios
- **Steam Authentication**: Confirma necessidade de login
- **Session Hijacking**: Testa validação de sessão

### ✅ **Rate Limiting e DoS:**
- **Payment Spam**: Verifica limitação de requests de pagamento
- **Rapid Withdrawals**: Testa proteção contra saque em massa

### ✅ **Lógica de Negócio:**
- **Double Spending**: Impede uso duplo do mesmo item
- **Race Conditions**: Testa condições de corrida em transações

## 🚨 **VULNERABILIDADES CRÍTICAS TESTADAS**

### **Cenário 1: Atacante Altera PIX no Request**
```javascript
// ❌ ATAQUE: Usuário intercepta e altera dados
req.body.pagamento.chave_pix = '11999999999' // PIX do atacante
// ✅ PROTEÇÃO: Server-side validation deve rejeitar
```

### **Cenário 2: Tentativa de Saque Não Autorizado**
```javascript
// ❌ ATAQUE: Sacar de outro usuário
{ steamid: '76561199999999999', valor: 100.00 }
// ✅ PROTEÇÃO: Verificação steamid vs sessão
```

### **Cenário 3: SQL Injection em Pagamento**
```javascript
// ❌ ATAQUE: Injeção SQL
chave_pix: '"; DROP TABLE informacoes_pagamento; --'
// ✅ PROTEÇÃO: Sanitização e ORM
```

## 📊 **INTERPRETANDO RESULTADOS**

### **✅ PROTEÇÃO FUNCIONANDO:**
```
✅ PROTECTION: Request properly rejected (Status: 400/401/403)
✅ Malicious payment rejected
✅ Trade Hold protection active
✅ CSRF protection working
✅ Authentication protection active
```

### **❌ VULNERABILIDADE CRÍTICA:**
```
❌ VULNERABILITY: Malicious request accepted (Status: 200)
❌ SECURITY BREACH: Payment manipulation succeeded
❌ CRITICAL: Authentication bypassed
```

## 🔧 **CONFIGURAÇÃO PARA PRODUÇÃO**

### **Cypress Config (cypress.config.js)**
```javascript
module.exports = {
  e2e: {
    baseUrl: 'https://your-production-url.herokuapp.com',
    env: {
      test_mode: true
    }
  }
}
```

### **⚠️ IMPORTANTE: Variáveis de Teste**
```bash
# NUNCA usar credenciais reais em testes!
TEST_PIX_KEY=12345678900  # PIX fake para testes
TEST_STEAM_ID=76561199063085722  # Steam ID de teste
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