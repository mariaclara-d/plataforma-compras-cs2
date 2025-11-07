#  GUIA DE SEGURANÇA PARA PRODUÇÃO

##  CHECKLIST PRÉ-DEPLOY

### **Configuração de Ambiente**
- [ ] `.env.production` configurado com valores reais
- [ ] `SECRET_KEY` gerada com 32+ caracteres aleatórios
- [ ] `FLASK_DEBUG=false` em produção
- [ ] `FLASK_ENV=production` definido
- [ ] Variáveis sensíveis não estão no código fonte

### **Banco de Dados**
- [ ] PostgreSQL configurado para produção
- [ ] Credenciais de DB seguras e complexas
- [ ] Backup automático configurado
- [ ] SSL/TLS habilitado para conexões DB
- [ ] Migrations aplicadas corretamente

### **Autenticação e Sessões**
- [ ] Steam API keys válidas e ativas
- [ ] Session cookies com `Secure` e `HttpOnly`
- [ ] Timeout de sessão configurado (24h max)
- [ ] Rate limiting em rotas de login
- [ ] Validação de session tokens HMAC

### **Admin e Privilégios**
- [ ] Senha padrão admin removida
- [ ] Admin criado com senha forte (8+ chars, complexa)
- [ ] Rate limiting em rotas admin (5 tentativas/5min)
- [ ] Logs de auditoria para ações admin
- [ ] MFA considerado para admin (futuro)

### **Headers de Segurança**
- [ ] Content Security Policy (CSP) restritiva
- [ ] HTTP Strict Transport Security (HSTS)
- [ ] X-Frame-Options: DENY
- [ ] X-Content-Type-Options: nosniff
- [ ] Referrer-Policy: strict-origin-when-cross-origin

### **Rate Limiting**
- [ ] Rate limiting global: 100 req/hora
- [ ] Auth endpoints: 5 tentativas/5min
- [ ] Admin endpoints: 5 tentativas/5min
- [ ] API endpoints: 30-60 req/min
- [ ] Redis configurado para persistência

### **Logs e Monitoramento**
- [ ] Logs estruturados e rotativos
- [ ] Logs de segurança separados
- [ ] Monitoramento de tentativas de login
- [ ] Alertas para ações admin suspeitas
- [ ] Logs de rate limiting

##  VULNERABILIDADES CRÍTICAS CORRIGIDAS

### **1. SECRET_KEY Hardcoded**  CORRIGIDO
- **Problema**: Chave secreta exposta no código
- **Solução**: Validação e geração automática segura
- **Verificação**: `check_secret_key()` em `app.py`

### **2. Autenticação Insegura**  CORRIGIDO
- **Problema**: Sessions sem validação HMAC
- **Solução**: Tokens HMAC com validação temporal
- **Verificação**: `utils/auth_helpers.py`

### **3. Rate Limiting Ausente**  CORRIGIDO
- **Problema**: Sem proteção contra brute force
- **Solução**: Rate limiting baseado em sliding window
- **Verificação**: `middleware/rate_limiting.py`

### **4. Admin Senha Padrão**  CORRIGIDO
- **Problema**: Credenciais admin/admin123
- **Solução**: Criação forçada de senha forte
- **Verificação**: `scripts/create_admin.py`

### **5. CSP Permissiva**  CORRIGIDO
- **Problema**: 'unsafe-inline' no CSP
- **Solução**: CSP restritiva sem inline
- **Verificação**: `middleware/security_headers.py`

##  COMANDOS DE DEPLOY SEGURO

### **1. Preparação do Ambiente**
```bash
# Copiar template de produção
cp .env.production.template .env.production

# Gerar SECRET_KEY segura
python -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))" >> .env.production

# Configurar permissões
chmod 600 .env.production
```

### **2. Criar Admin Seguro**
```bash
# Executar script de criação segura
python scripts/create_admin.py

# O script irá solicitar:
# - Username (min 3 chars)
# - Senha forte (min 8 chars, complexa)
# - Confirmação de senha
```

### **3. Verificação de Segurança**
```bash
# Testar configurações
python -c "from app import create_app; app = create_app(); print(' App configurada corretamente')"

# Verificar SECRET_KEY
python -c "import os; print(' SECRET_KEY configurada' if os.getenv('SECRET_KEY') and len(os.getenv('SECRET_KEY')) >= 32 else ' SECRET_KEY inválida')"

# Testar autenticação
python simple_auth_test.py
```

##  CONFIGURAÇÕES DE SERVIDOR

### **Nginx (Proxy Reverso)**
```nginx
server {
    listen 443 ssl http2;
    server_name seudominio.com;
    
    ssl_certificate /etc/ssl/certs/seudominio.crt;
    ssl_certificate_key /etc/ssl/private/seudominio.key;
    
    # Cabeçalhos de segurança
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    
    # Rate limiting no Nginx
    limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;
    limit_req_zone $binary_remote_addr zone=api:10m rate=30r/m;
    
    location /auth/ {
        limit_req zone=login burst=5 nodelay;
        proxy_pass http://127.0.0.1:5000;
    }
    
    location /api/ {
        limit_req zone=api burst=10 nodelay;
        proxy_pass http://127.0.0.1:5000;
    }
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### **Firewall (UFW)**
```bash
# Configurar firewall
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

### **Systemd Service**
```ini
[Unit]
Description=Flask CS2 Marketplace
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/cs2-marketplace
Environment=PATH=/var/www/cs2-marketplace/venv/bin
ExecStart=/var/www/cs2-marketplace/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

##  MONITORAMENTO E ALERTAS

### **Logs Importantes**
- `logs/security.log` - Tentativas de login, admin actions
- `logs/error.log` - Erros de aplicação
- `logs/performance.log` - Performance metrics
- `logs/app.log` - Logs gerais

### **Alertas Recomendados**
- Múltiplas tentativas de login falhadas
- Ações admin fora do horário normal
- Erros de rate limiting excessivos
- Falhas de conexão com Steam API
- Uso de CPU/memória alto

##  TESTES DE SEGURANÇA

### **Testes Manuais**
```bash
# Teste de rate limiting
for i in {1..10}; do curl -X POST http://localhost:5000/auth/login; done

# Teste de headers de segurança
curl -I http://localhost:5000

# Teste de admin sem auth
curl http://localhost:5000/admin/dashboard

# Teste de SQL injection (deve falhar)
curl "http://localhost:5000/api/user/'; DROP TABLE users; --/balance"
```

### **Ferramentas Recomendadas**
- OWASP ZAP - Teste de penetração
- nmap - Port scanning
- sqlmap - SQL injection testing
- Burp Suite - Web application testing

##  MANUTENÇÃO CONTÍNUA

### **Atualizações de Segurança**
- Atualizar dependências mensalmente
- Monitorar CVEs das bibliotecas usadas
- Aplicar patches de segurança rapidamente
- Revisar logs semanalmente

### **Backup e Recovery**
- Backup diário do banco de dados
- Backup semanal completo da aplicação
- Testar restore mensalmente
- Documentar procedimentos de recovery

### **Auditoria de Código**
- Review de código para novas features
- Scan automático de vulnerabilidades
- Penetration testing trimestral
- Auditoria de logs mensalmente

---

**IMPORTANTE**: Este guia cobre os aspectos críticos de segurança. Para ambientes de alta criticidade, considere contratar uma auditoria de segurança profissional.
