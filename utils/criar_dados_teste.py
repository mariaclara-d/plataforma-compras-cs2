#!/usr/bin/env python3
"""
Script para testar e criar dados de saques para teste do admin
"""

import os
import sys
sys.path.insert(0, '/app')

# Configuração do ambiente
os.environ['DATABASE_URL'] = 'postgresql://postgres:dba0c4@db:5432/csgo_skins'
os.environ['FLASK_ENV'] = 'production'

from app import create_app
from models.saques import Saque
from db_config import db
from datetime import datetime

def criar_saques_teste():
    """Cria alguns saques de teste"""
    app = create_app()
    
    with app.app_context():
        print("🧪 Criando dados de teste para saques...")
        
        # Limpar saques existentes (opcional)
        # Saque.query.delete()
        
        # Criar saques de teste
        saques_teste = [
            {
                'steamid': '76561198123456789',
                'valor': 25.50,
                'status': 'pendente'
            },
            {
                'steamid': '76561198987654321', 
                'valor': 50.00,
                'status': 'processado'
            },
            {
                'steamid': '76561198555666777',
                'valor': 15.75,
                'status': 'pendente'
            },
            {
                'steamid': '76561198888999000',
                'valor': 100.00,
                'status': 'cancelado'
            }
        ]
        
        for saque_data in saques_teste:
            # Verificar se já existe
            existing = Saque.query.filter_by(steamid=saque_data['steamid']).first()
            if not existing:
                saque = Saque(
                    steamid=saque_data['steamid'],
                    valor=saque_data['valor'],
                    status=saque_data['status'],
                    criado_em=datetime.utcnow(),
                    atualizado_em=datetime.utcnow()
                )
                db.session.add(saque)
                print(f"✅ Saque criado: {saque_data['steamid']} - R$ {saque_data['valor']} ({saque_data['status']})")
            else:
                print(f"⚠️ Saque já existe: {saque_data['steamid']}")
        
        # Salvar no banco
        db.session.commit()
        
        # Verificar total
        total = Saque.query.count()
        pendentes = Saque.query.filter_by(status='pendente').count()
        processados = Saque.query.filter_by(status='processado').count()
        
        print(f"\n📊 Estatísticas:")
        print(f"   Total de saques: {total}")
        print(f"   Pendentes: {pendentes}")
        print(f"   Processados: {processados}")
        
        print("\n🎉 Dados de teste criados com sucesso!")

if __name__ == '__main__':
    criar_saques_teste()
