#!/usr/bin/env python3
"""
Script para criar o primeiro usuário admin no Docker/PostgreSQL
"""

import sys
import os
from pathlib import Path

# Adiciona o diretório raiz ao PYTHONPATH
sys.path.insert(0, '/app')

# Força o uso do PostgreSQL no Docker
os.environ['DATABASE_URL'] = 'postgresql://postgres:dba0c4@db:5432/csgo_skins'
os.environ['FLASK_ENV'] = 'production'

from app import create_app
from models.admin import Admin
from db_config import db

def create_first_admin():
    """Cria o primeiro usuário admin"""
    
    app = create_app()
    
    with app.app_context():
        try:
            # Verifica se já existe admin
            existing_admin = Admin.query.first()
            if existing_admin:
                print("❌ Já existe um admin cadastrado:")
                print(f"   Username: {existing_admin.username}")
                print(f"   Criado em: {existing_admin.created_at}")
                return False
            
            # Cria o primeiro admin
            admin = Admin(username='admin')
            admin.set_password('admin123')  # Senha padrão
            admin.is_active = True
            
            db.session.add(admin)
            db.session.commit()
            
            print("✅ Primeiro admin criado com sucesso!")
            print("   Username: admin")
            print("   Password: admin123")
            print("   🔗 Acesse: http://localhost:5000/admin")
            print("")
            print("⚠️  IMPORTANTE: Troque a senha após o primeiro login!")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao acessar banco: {str(e)}")
            print("🔧 Tentando criar as tabelas primeiro...")
            
            # Tenta criar as tabelas
            db.create_all()
            
            # Tenta novamente
            admin = Admin(username='admin')
            admin.set_password('admin123')
            admin.is_active = True
            
            db.session.add(admin)
            db.session.commit()
            
            print("✅ Tabelas criadas e admin configurado!")
            print("   Username: admin")
            print("   Password: admin123")
            print("   🔗 Acesse: http://localhost:5000/admin")
            
            return True

if __name__ == '__main__':
    print("🔧 Criando primeiro usuário admin no PostgreSQL...")
    print("")
    
    try:
        success = create_first_admin()
        if success:
            print("🎯 Admin criado com sucesso!")
        else:
            print("ℹ️  Admin já existe no sistema")
            
    except Exception as e:
        print(f"❌ Erro ao criar admin: {str(e)}")
        import traceback
        traceback.print_exc()
