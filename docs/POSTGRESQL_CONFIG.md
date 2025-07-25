# 🗄️ CONFIGURAÇÃO POSTGRESQL PARA PRODUÇÃO

## 📋 Variáveis de Ambiente Necessárias

### Para Heroku PostgreSQL:
```bash
# Heroku configura automaticamente DATABASE_URL
DATABASE_URL=postgresql://username:password@hostname:port/database_name

# Exemplo real Heroku:
DATABASE_URL=postgresql://u123abc:p456def@ec2-hostname.compute-1.amazonaws.com:5432/d789ghi
```

### Para PostgreSQL Local/VPS:
```bash
# Configuração manual
DB_HOST=localhost
DB_PORT=5432
DB_NAME=csgo_skins_prod
DB_USER=csgo_user
DB_PASSWORD=sua_senha_super_segura
```

## ⚙️ Configuração no Flask

### 1. Arquivo .env para Produção
```bash
# .env.production
FLASK_ENV=production
DEBUG=False

# PostgreSQL Heroku (automático)
DATABASE_URL=postgresql://...

# OU PostgreSQL manual
SQLALCHEMY_DATABASE_URI=postgresql://user:pass@host:port/dbname

# Pool de conexões
SQLALCHEMY_ENGINE_OPTIONS={"pool_pre_ping": true, "pool_recycle": 300}
```

### 2. Configuração no app.py
```python
import os
from urllib.parse import urlparse

def get_database_url():
    """Obtém URL do banco de acordo com o ambiente"""
    
    # Heroku fornece DATABASE_URL automaticamente
    database_url = os.getenv('DATABASE_URL')
    
    if database_url:
        # Heroku usa postgres:// mas SQLAlchemy precisa postgresql://
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        return database_url
    
    # Configuração manual para outros ambientes
    db_host = os.getenv('DB_HOST', 'localhost')
    db_port = os.getenv('DB_PORT', '5432')
    db_name = os.getenv('DB_NAME', 'csgo_skins')
    db_user = os.getenv('DB_USER', 'postgres')
    db_password = os.getenv('DB_PASSWORD', '')
    
    return f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
```

## 🚀 Configuração para Heroku

### 1. Addon PostgreSQL
```bash
# Criar app Heroku
heroku create seu-app-csgo

# Adicionar PostgreSQL (plano gratuito)
heroku addons:create heroku-postgresql:mini

# Verificar configuração
heroku config:get DATABASE_URL
```

### 2. requirements.txt
```
psycopg2-binary==2.9.7
Flask-SQLAlchemy==3.0.5
Flask-Migrate==4.0.5
```

### 3. Procfile
```
web: python app.py
release: flask db upgrade
```

## 🔧 Scripts de Migração

### 1. Inicializar Migrações
```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

### 2. Deploy com Migração
```bash
git push heroku main
# Heroku executa automaticamente: flask db upgrade
```

## 📊 Schema PostgreSQL Otimizado

### Índices Recomendados:
```sql
-- Índices para performance
CREATE INDEX idx_users_steam_id ON users(steam_id);
CREATE INDEX idx_trade_offers_status ON trade_offers(status);
CREATE INDEX idx_transacoes_user_id ON transacoes(user_id);
CREATE INDEX idx_transacoes_data ON transacoes(data_transacao);
CREATE INDEX idx_skins_preco ON skins(preco);

-- Índices compostos
CREATE INDEX idx_trade_offers_user_status ON trade_offers(user_id, status);
CREATE INDEX idx_transacoes_user_data ON transacoes(user_id, data_transacao);
```

### Configurações PostgreSQL:
```sql
-- Para produção
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';
ALTER SYSTEM SET max_connections = 100;
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET work_mem = '4MB';
```

## 🔒 Segurança PostgreSQL

### 1. Usuário Dedicado
```sql
-- Criar usuário específico para a aplicação
CREATE USER csgo_app WITH PASSWORD 'senha_super_segura';
CREATE DATABASE csgo_skins OWNER csgo_app;

-- Permissões mínimas
GRANT CONNECT ON DATABASE csgo_skins TO csgo_app;
GRANT USAGE ON SCHEMA public TO csgo_app;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO csgo_app;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO csgo_app;
```

### 2. SSL/TLS
```bash
# Forçar SSL (Heroku faz automaticamente)
PGSSLMODE=require
```

## 📈 Monitoramento

### 1. Queries Lentas
```sql
-- Habilitar log de queries lentas
ALTER SYSTEM SET log_min_duration_statement = 1000; -- 1 segundo
```

### 2. Estatísticas
```sql
-- Ver queries mais executadas
SELECT query, calls, total_time, mean_time 
FROM pg_stat_statements 
ORDER BY total_time DESC LIMIT 10;
```

## 🔄 Backup Automático

### Para Heroku:
```bash
# Backup manual
heroku pg:backups:capture

# Agendar backup automático
heroku pg:backups:schedule DATABASE_URL --at '02:00 America/Sao_Paulo'
```

### Para VPS:
```bash
# Crontab para backup diário
0 2 * * * pg_dump -h localhost -U csgo_app csgo_skins | gzip > /backups/backup_$(date +\%Y\%m\%d).sql.gz
```

---

## ⚡ Diferenças Principais PostgreSQL vs SQLite

| Aspecto | SQLite | PostgreSQL |
|---------|---------|------------|
| **Conexões** | Arquivo local | Rede TCP/IP |
| **Concurrent Users** | Limitado | Ilimitado |
| **Transações** | Básicas | ACID completo |
| **Índices** | Básicos | Avançados (GIN, GiST) |
| **Escalabilidade** | Baixa | Alta |
| **Backup** | Cópia arquivo | pg_dump/restore |
| **Monitoramento** | Limitado | Completo |

PostgreSQL é **essencial** para produção com múltiplos usuários!
