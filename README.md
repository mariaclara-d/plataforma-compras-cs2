# 🔐 CS2 Marketplace - Flask Application

[![Security Status](https://img.shields.io/badge/Security-Hardened-green.svg)](docs/SECURITY_PRODUCTION_GUIDE.md)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.0+-red.svg)](https://flask.palletsprojects.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Uma plataforma segura para marketplace de itens CS2 com integração Steam e sistema de trading avançado.

## 🚀 **CARACTERÍSTICAS PRINCIPAIS**

### **Segurança Empresarial** 🔐
- ✅ Autenticação Steam OpenID com tokens HMAC
- ✅ Rate limiting avançado (sliding window)
- ✅ Headers de segurança (CSP, HSTS, X-Frame-Options)
- ✅ Validação e sanitização completa de inputs
- ✅ Proteção contra XSS, SQL Injection e CSRF
- ✅ Sistema de admin com auditoria completa

### **Sistema de Trading** 💱
- 🔄 Integração completa com Steam Web API
- 📦 Gerenciamento de inventário em tempo real
- 💰 Sistema de saldos e transações
- 🔒 Trade holds e proteção anti-fraude
- � Dashboard administrativo avançado

## 🔧 **INSTALAÇÃO RÁPIDA**

```
📂 raiz/
├── 🏠 Arquivos Principais
│   ├── app.py              # Aplicação Flask principal
│   ├── main.py             # Ponto de entrada alternativo  
│   ├── db_config.py        # Configuração inteligente do banco
│   ├── requirements.txt    # Dependências Python
│   ├── Procfile           # Configuração Heroku
│   ├── docker-compose.yml # Orquestração Docker
│   └── Dockerfile         # Container da aplicação
│
├── 📂 Código da Aplicação
│   ├── models/            # Modelos SQLAlchemy
│   ├── routes/            # Rotas da aplicação  
│   ├── services/          # Serviços de negócio
│   ├── middleware/        # Middleware de segurança
│   ├── templates/         # Templates HTML/Jinja2
│   └── static/           # Arquivos estáticos (CSS/JS/img)
│
├── 📂 Configuração
│   ├── config/           # Configurações gerais
│   │   ├── logging_config.py
│   │   └── steam/        # Configurações Steam
│   ├── .env.example      # Template de variáveis
│   ├── .env.production   # Config produção
│   └── migrations/       # Migrações Alembic
│
├── 📂 Scripts e Automação
│   ├── scripts/          # Scripts utilitários
│   │   ├── backup_*.py   # Backup do banco
│   │   ├── create_admin*.py # Criação de admin
│   │   ├── migrate_*.py  # Migração de dados
│   │   └── start_*.bat   # Scripts inicialização
│   ├── deploy/           # Deploy e CI/CD
│   │   ├── deploy_heroku.ps1 # Script deploy automatizado
│   │   └── CHECKLIST_DEPLOY.md # Guia passo-a-passo
│   └── utils/            # Utilitários diversos
│
├── 📂 Documentação
│   ├── docs/             # Documentação técnica
│   │   ├── README.md     # Documentação completa
│   │   ├── DOCKER_COMMANDS.md
│   │   ├── POSTGRESQL_CONFIG.md
│   │   └── SECURITY_AUDIT.md
│   └── utils/ESTRUTURA_PROJETO.md # Este arquivo
│
└── 📂 Dados e Logs
    ├── instance/         # Dados da instância
    ├── logs/            # Logs da aplicação
    └── backups/         # Backups do banco
```

## ⚡ Início Rápido

### Desenvolvimento Local
```bash
# Ambiente Docker (Recomendado)
docker-compose up -d

# Ou ambiente Python local
python app.py
```

### Acesso ao Sistema
- **Site:** http://localhost:5000
- **Admin:** http://localhost:5000/admin/login
  - User: `admin` / Password: `admin123`

## 📚 Documentação

- 📖 [**Documentação Completa**](docs/README.md)
- 🚀 [**Guia de Deploy**](deploy/CHECKLIST_DEPLOY.md)  
- 🐳 [**Comandos Docker**](docs/DOCKER_COMMANDS.md)
- 🔒 [**Auditoria de Segurança**](docs/SECURITY_AUDIT.md)
- 🗃️ [**Configuração PostgreSQL**](docs/POSTGRESQL_CONFIG.md)

## 🛠️ Scripts Úteis

```bash
# Inicializar ambiente
.\scripts\start_admin.ps1

# Criar backup do banco  
python scripts\backup_postgresql.py

# Reset completo do banco
python scripts\reset_db.py

# Criar usuário admin
python scripts\create_admin.py
```

## 🎯 Status do Projeto

- ✅ **Sistema Admin:** Funcionando
- ✅ **Banco PostgreSQL:** Configurado
- ✅ **Docker:** Operacional
- ✅ **Segurança:** Auditada
- 🚀 **Deploy:** Pronto para Heroku

## 🔗 Links Importantes

- [Heroku Dashboard](https://dashboard.heroku.com)
- [Steam API Documentation](https://developer.valvesoftware.com/wiki/Steam_Web_API)
- [CS2 Items Database](https://steamcommunity.com/market/search?appid=730)

---

**📧 Contato:** [mariaclara-d](https://github.com/mariaclara-d)  
**🏷️ Versão:** 1.0.0  
**📅 Última atualização:** $(Get-Date -Format "dd/MM/yyyy")
