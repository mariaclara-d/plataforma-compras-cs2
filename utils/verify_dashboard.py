#!/usr/bin/env python3
"""
Script para verificar se as mudanças foram aplicadas no container
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
from models.saques import Saque
from models.trade_offers import TradeOffer

def check_dashboard_config():
    """Verifica se o dashboard está configurado corretamente"""
    
    app = create_app()
    
    with app.app_context():
        print("🔍 Verificando configuração do dashboard...")
        
        # Teste 1: Verificar atributos do modelo Saque
        print("\n1. Atributos do modelo Saque:")
        saque_attrs = [attr for attr in dir(Saque) if not attr.startswith('_')]
        for attr in saque_attrs:
            print(f"   ✅ {attr}")
        
        if 'criado_em' in saque_attrs:
            print("   ✅ Atributo 'criado_em' encontrado!")
        else:
            print("   ❌ Atributo 'criado_em' NÃO encontrado!")
            
        if 'created_at' in saque_attrs:
            print("   ❌ Atributo 'created_at' ainda existe (PROBLEMA!)")
        else:
            print("   ✅ Atributo 'created_at' não existe (correto)")
        
        # Teste 2: Simular dashboard com dados seguros
        print("\n2. Simulando dashboard:")
        try:
            total_saques = Saque.query.count()
            saques_pendentes = Saque.query.filter_by(status='pendente').count()
            valor_saques_pendente = 0.0
            
            print(f"   ✅ Total saques: {total_saques}")
            print(f"   ✅ Saques pendentes: {saques_pendentes}")
            print(f"   ✅ Valor pendente: R$ {valor_saques_pendente:.2f}")
            
            # Teste específico da query que falha
            print("\n3. Testando query problemática:")
            saques_recentes = Saque.query.order_by(Saque.criado_em.desc()).limit(5).all()
            print(f"   ✅ Query de saques recentes funcionou: {len(saques_recentes)} resultados")
            
        except Exception as e:
            print(f"   ❌ Erro na simulação: {str(e)}")
        
        print("\n✅ Verificação concluída!")

if __name__ == '__main__':
    check_dashboard_config()
