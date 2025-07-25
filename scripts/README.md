# 📁 Scripts - Automação e Utilitários

Esta pasta contém scripts para automação e gerenciamento do sistema.

## 🗄️ Scripts de Banco de Dados
- **`backup_db.py`** - Backup do banco SQLite
- **`backup_postgresql.py`** - Backup do PostgreSQL
- **`migrate_to_postgresql.py`** - Migração SQLite → PostgreSQL
- **`reset_db.py`** - Reset completo do banco

## 👤 Scripts de Administração
- **`create_admin.py`** - Criar usuário admin (local)
- **`create_admin_docker.py`** - Criar usuário admin (Docker)
- **`popular_teste.py`** - Popular banco com dados de teste

## 🚀 Scripts de Inicialização
- **`start.bat`** - Iniciar sistema (Windows)
- **`start_admin.bat`** - Iniciar com usuário admin
- **`start_admin.ps1`** - Iniciar via PowerShell

## 📋 Como Usar

```bash
# Backup do banco
python scripts/backup_postgresql.py

# Criar admin
python scripts/create_admin.py

# Reset banco (CUIDADO!)
python scripts/reset_db.py

# Iniciar sistema
./scripts/start_admin.ps1
```
