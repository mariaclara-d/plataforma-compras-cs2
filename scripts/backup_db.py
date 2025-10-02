#!/usr/bin/env python3
"""
Script de backup do banco de dados
Cria backup completo do banco SQLite local
"""
import sqlite3
import os
import shutil
from datetime import datetime
from pathlib import Path

def create_database_backup():
    """Cria backup completo do banco de dados"""
    print(" INICIANDO BACKUP DO BANCO DE DADOS")
    print("=" * 50)
    
    # Caminhos
    db_path = Path("instance/users.db")
    backup_dir = Path("backups")
    
    # Criar diretório de backup
    backup_dir.mkdir(exist_ok=True)
    
    # Nome do backup com timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"users_backup_{timestamp}.db"
    backup_path = backup_dir / backup_filename
    
    try:
        if not db_path.exists():
            print(" Banco de dados não encontrado!")
            return False
            
        # Criar backup usando SQLite backup API
        print(f" Fonte: {db_path}")
        print(f" Destino: {backup_path}")
        
        # Conectar ao banco original
        source_conn = sqlite3.connect(str(db_path))
        
        # Criar conexão para backup
        backup_conn = sqlite3.connect(str(backup_path))
        
        # Executar backup
        source_conn.backup(backup_conn)
        
        # Fechar conexões
        source_conn.close()
        backup_conn.close()
        
        # Verificar se backup foi criado
        if backup_path.exists():
            size_mb = backup_path.stat().st_size / (1024 * 1024)
            print(f" Backup criado com sucesso!")
            print(f" Tamanho: {size_mb:.2f} MB")
            print(f" Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
            
            # Criar link simbólico para o backup mais recente
            latest_path = backup_dir / "latest_backup.db"
            if latest_path.exists():
                latest_path.unlink()
            
            # No Windows, usar copy ao invés de symlink
            shutil.copy2(backup_path, latest_path)
            print(f" Link criado: {latest_path}")
            
            return True
        else:
            print(" Falha ao criar backup!")
            return False
            
    except Exception as e:
        print(f" Erro durante backup: {e}")
        return False

def list_backups():
    """Lista todos os backups disponíveis"""
    backup_dir = Path("backups")
    
    if not backup_dir.exists():
        print(" Nenhum backup encontrado")
        return
    
    backups = list(backup_dir.glob("users_backup_*.db"))
    
    if not backups:
        print(" Nenhum backup encontrado")
        return
    
    print("\n BACKUPS DISPONÍVEIS:")
    print("-" * 50)
    
    for backup in sorted(backups, reverse=True):
        size_mb = backup.stat().st_size / (1024 * 1024)
        mtime = datetime.fromtimestamp(backup.stat().st_mtime)
        print(f" {backup.name}")
        print(f"    Tamanho: {size_mb:.2f} MB")
        print(f"    Criado: {mtime.strftime('%d/%m/%Y %H:%M:%S')}")
        print()

def restore_backup(backup_name=None):
    """Restaura um backup específico"""
    backup_dir = Path("backups")
    
    if backup_name:
        backup_path = backup_dir / backup_name
    else:
        backup_path = backup_dir / "latest_backup.db"
    
    if not backup_path.exists():
        print(f" Backup não encontrado: {backup_path}")
        return False
    
    db_path = Path("instance/users.db")
    
    try:
        # Criar backup do banco atual antes de restaurar
        if db_path.exists():
            current_backup = db_path.with_suffix('.db.bak')
            shutil.copy2(db_path, current_backup)
            print(f" Backup atual salvo como: {current_backup}")
        
        # Restaurar backup
        shutil.copy2(backup_path, db_path)
        print(f" Backup restaurado com sucesso!")
        print(f" De: {backup_path}")
        print(f" Para: {db_path}")
        
        return True
        
    except Exception as e:
        print(f" Erro ao restaurar backup: {e}")
        return False

def main():
    """Função principal"""
    import sys
    
    if len(sys.argv) < 2:
        print("Uso: python backup_db.py [create|list|restore] [backup_name]")
        print("  create  - Criar novo backup")
        print("  list    - Listar backups disponíveis")
        print("  restore - Restaurar backup (último ou especificado)")
        return
    
    command = sys.argv[1]
    
    if command == "create":
        create_database_backup()
    elif command == "list":
        list_backups()
    elif command == "restore":
        backup_name = sys.argv[2] if len(sys.argv) > 2 else None
        restore_backup(backup_name)
    else:
        print(f" Comando desconhecido: {command}")

if __name__ == "__main__":
    main()
