#!/usr/bin/env python3
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
