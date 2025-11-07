#!/usr/bin/env python3
"""
Script para criar o primeiro usuário admin
"""

import sys
import os
from pathlib import Path

# Adiciona o diretório raiz ao PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent))

# Configurar environment
os.environ['FLASK_ENV'] = 'development'

from app import create_app
from models.admin import Admin
from db_config import db

def create_first_admin():
    """Cria o primeiro usuário admin com senha segura"""
    
    app = create_app()
    
    with app.app_context():
        # Verifica se já existe admin
        existing_admin = Admin.query.first()
        if existing_admin:
            print(" Já existe um admin cadastrado:")
            print(f"   Username: {existing_admin.username}")
            print(f"   Criado em: {existing_admin.created_at}")
            return False
        
        print(" Criando primeiro administrador...")
        
        # Solicitar dados do admin
        import getpass
        
        username = input("Username para admin: ").strip()
        if not username or len(username) < 3:
            print(" Username deve ter pelo menos 3 caracteres")
            return False
        
        print("  A senha deve ter pelo menos 8 caracteres, incluindo:")
        print("   - Letras maiúsculas e minúsculas")
        print("   - Números")
        print("   - Símbolos")
        
        while True:
            password = getpass.getpass("Digite senha segura para admin: ")
            password_confirm = getpass.getpass("Confirme a senha: ")
            
            if password != password_confirm:
                print(" Senhas não coincidem. Tente novamente.")
                continue
            
            # Validar força da senha
            if not validate_password_strength(password):
                print(" Senha não atende aos critérios de segurança. Tente novamente.")
                continue
            
            break
        
        # Cria o admin
        admin = Admin(username=username)
        admin.set_password(password)
        admin.is_active = True
        
        db.session.add(admin)
        db.session.commit()
        
        print(" Administrador criado com sucesso!")
        print(f"   Username: {username}")
        print("    Acesse: http://localhost:5000/admin")
        print("")
        print(" IMPORTANTE:")
        print("   - Guarde a senha em local seguro")
        print("   - Considere ativar 2FA em produção")
        print("   - Monitore logs de acesso admin")
        
        return True

def validate_password_strength(password):
    """Valida força da senha"""
    import re
    
    if len(password) < 8:
        print("    Senha deve ter pelo menos 8 caracteres")
        return False
    
    if not re.search(r'[A-Z]', password):
        print("    Senha deve conter pelo menos uma letra maiúscula")
        return False
    
    if not re.search(r'[a-z]', password):
        print("    Senha deve conter pelo menos uma letra minúscula")
        return False
    
    if not re.search(r'\d', password):
        print("    Senha deve conter pelo menos um número")
        return False
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        print("    Senha deve conter pelo menos um símbolo")
        return False
    
    # Verificar sequências comuns
    common_sequences = ['123456', 'abcdef', 'qwerty', 'password', 'admin']
    for seq in common_sequences:
        if seq.lower() in password.lower():
            print(f"    Senha não pode conter sequências comuns como '{seq}'")
            return False
    
    return True

if __name__ == '__main__':
    print(" Criando primeiro usuário admin...")
    print("")
    
    try:
        success = create_first_admin()
        if success:
            print(" Admin criado com sucesso!")
        else:
            print("ℹ  Admin já existe no sistema")
            
    except Exception as e:
        print(f" Erro ao criar admin: {str(e)}")
        import traceback
        traceback.print_exc()
