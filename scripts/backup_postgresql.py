#!/usr/bin/env python3
"""
Script de backup para PostgreSQL
Cria dumps do banco de dados para migração e backup
"""
import os
import subprocess
import datetime
from pathlib import Path
import shutil

def create_backup_directory():
    """Cria diretório de backup se não existir"""
    backup_dir = Path('backups')
    backup_dir.mkdir(exist_ok=True)
    return backup_dir

def backup_postgresql_database():
    """Faz backup do banco PostgreSQL"""
    print(" BACKUP POSTGRESQL")
    print("=" * 50)
    
    backup_dir = create_backup_directory()
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Configurações do banco (ajustar conforme necessário)
    db_config = {
        'host': 'localhost',
        'port': '5432',
        'database': 'csgo_skins',
        'username': 'postgres',
        'password': 'sua_senha_aqui'  # Ajustar
    }
    
    backup_file = backup_dir / f"backup_postgresql_{timestamp}.sql"
    
    try:
        # Comando pg_dump
        cmd = [
            'pg_dump',
            f"--host={db_config['host']}",
            f"--port={db_config['port']}",
            f"--username={db_config['username']}",
            '--format=custom',
            '--verbose',
            '--file', str(backup_file),
            db_config['database']
        ]
        
        print(f" Criando backup: {backup_file}")
        
        # Definir senha via variável de ambiente
        env = os.environ.copy()
        env['PGPASSWORD'] = db_config['password']
        
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f" Backup criado com sucesso!")
            print(f" Arquivo: {backup_file}")
            print(f" Tamanho: {backup_file.stat().st_size / 1024:.2f} KB")
            return str(backup_file)
        else:
            print(f" Erro no backup: {result.stderr}")
            return None
            
    except FileNotFoundError:
        print(" pg_dump não encontrado. Instale PostgreSQL client tools.")
        print(" Windows: Baixe PostgreSQL e adicione ao PATH")
        print(" Ubuntu: sudo apt-get install postgresql-client")
        return None
    except Exception as e:
        print(f" Erro: {e}")
        return None

def backup_sqlite_to_sql():
    """Faz backup do SQLite atual para migração"""
    print("\n BACKUP SQLITE PARA MIGRAÇÃO")
    print("=" * 50)
    
    backup_dir = create_backup_directory()
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    sqlite_path = Path('instance/users.db')
    if not sqlite_path.exists():
        print(" Banco SQLite não encontrado")
        return None
    
    backup_file = backup_dir / f"migration_from_sqlite_{timestamp}.sql"
    
    try:
        # Comando sqlite3 para dump
        cmd = [
            'sqlite3',
            str(sqlite_path),
            '.dump'
        ]
        
        with open(backup_file, 'w', encoding='utf-8') as f:
            result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True)
        
        if result.returncode == 0:
            print(f" Dump SQLite criado!")
            print(f" Arquivo: {backup_file}")
            print(f" Tamanho: {backup_file.stat().st_size / 1024:.2f} KB")
            return str(backup_file)
        else:
            print(f" Erro no dump: {result.stderr}")
            return None
            
    except Exception as e:
        print(f" Erro: {e}")
        return None

def create_migration_script():
    """Cria script de migração SQLite -> PostgreSQL"""
    print("\n CRIANDO SCRIPT DE MIGRAÇÃO")
    print("=" * 50)
    
    migration_script = '''#!/usr/bin/env python3
"""
Script de migração de dados SQLite para PostgreSQL
Execute após configurar o banco PostgreSQL
"""
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime

def migrate_data():
    """Migra dados do SQLite para PostgreSQL"""
    
    # Configurações SQLite
    sqlite_path = 'instance/users.db'
    
    # Configurações PostgreSQL (ajustar conforme necessário)
    pg_config = {
        'host': 'localhost',
        'port': 5432,
        'database': 'csgo_skins',
        'user': 'postgres',
        'password': 'sua_senha_aqui'
    }
    
    try:
        # Conectar SQLite
        sqlite_conn = sqlite3.connect(sqlite_path)
        sqlite_conn.row_factory = sqlite3.Row
        
        # Conectar PostgreSQL
        pg_conn = psycopg2.connect(**pg_config)
        pg_cursor = pg_conn.cursor(cursor_factory=RealDictCursor)
        
        # Listar tabelas do SQLite
        sqlite_cursor = sqlite_conn.cursor()
        sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in sqlite_cursor.fetchall()]
        
        print(f" Migrando {len(tables)} tabelas...")
        
        for table in tables:
            if table == 'sqlite_sequence':
                continue
                
            print(f" Migrando tabela: {table}")
            
            # Ler dados do SQLite
            sqlite_cursor.execute(f"SELECT * FROM {table}")
            rows = sqlite_cursor.fetchall()
            
            if rows:
                # Preparar inserção no PostgreSQL
                columns = [description[0] for description in sqlite_cursor.description]
                placeholders = ', '.join(['%s'] * len(columns))
                
                insert_query = f"""
                INSERT INTO {table} ({', '.join(columns)}) 
                VALUES ({placeholders})
                ON CONFLICT DO NOTHING
                """
                
                # Inserir dados
                for row in rows:
                    try:
                        pg_cursor.execute(insert_query, row)
                    except Exception as e:
                        print(f" Erro na linha: {e}")
                
                pg_conn.commit()
                print(f" {len(rows)} registros migrados de {table}")
            else:
                print(f" Tabela {table} vazia")
        
        print(" Migração concluída!")
        
    except Exception as e:
        print(f" Erro na migração: {e}")
    finally:
        if 'sqlite_conn' in locals():
            sqlite_conn.close()
        if 'pg_conn' in locals():
            pg_conn.close()

if __name__ == "__main__":
    migrate_data()
'''
    
    with open('migrate_to_postgresql.py', 'w', encoding='utf-8') as f:
        f.write(migration_script)
    
    print(" Script de migração criado: migrate_to_postgresql.py")

def main():
    """Função principal"""
    print(" CONFIGURAÇÃO BANCO POSTGRESQL")
    print("=" * 60)
    
    # 1. Backup do banco atual (se PostgreSQL já existir)
    # backup_postgresql_database()
    
    # 2. Backup do SQLite para migração
    sqlite_backup = backup_sqlite_to_sql()
    
    # 3. Criar script de migração
    create_migration_script()
    
    print(f"\n RESUMO:")
    print(f" Backup SQLite: {'OK' if sqlite_backup else 'ERRO'}")
    print(f" Script migração: OK")
    print(f"\n PRÓXIMOS PASSOS:")
    print(f"1. Configurar PostgreSQL")
    print(f"2. Ajustar credenciais nos scripts")
    print(f"3. Executar: python migrate_to_postgresql.py")

if __name__ == "__main__":
    main()
