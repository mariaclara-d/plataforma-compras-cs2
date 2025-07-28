# routes/transactions.py
from flask import Blueprint, session, jsonify, request
from models.transacoes import Transacao
from models.saques import Saque
from services.trade_hold_service import TradeHoldService
from app import db
import logging

transactions_blueprint = Blueprint('transactions', __name__)
trade_hold_service = TradeHoldService()

@transactions_blueprint.route('/api/transactions/history')
def get_transaction_history():
    """Retorna o histórico de transações do usuário"""
    if 'steam_id' not in session:
        return jsonify({'success': False, 'message': 'Usuário não autenticado'}), 401
    
    try:
        user_steam_id = session['steam_id']
        
        # Buscar transações de venda
        transacoes = Transacao.query.filter_by(steamid=user_steam_id).order_by(Transacao.criado_em.desc()).all()
        
        # Buscar saques
        saques = Saque.query.filter_by(steamid=user_steam_id).order_by(Saque.criado_em.desc()).all()
        
        # Combinar e formatar dados
        transactions = []
        
        for transacao in transacoes:
            transactions.append({
                'id': transacao.id,
                'type': 'Venda de Skin',
                'amount': float(transacao.valor),
                'status': 'completed',
                'created_at': transacao.criado_em.isoformat(),
                'description': f"Transação #{transacao.id}"
            })
        
        for saque in saques:
            status_map = {
                'pendente': 'pending',
                'processando': 'processing', 
                'concluido': 'completed',
                'cancelado': 'cancelled'
            }
            
            transactions.append({
                'id': f"saque_{saque.id}",
                'type': 'Saque',
                'amount': -float(saque.valor),  # Negativo para saques
                'status': status_map.get(saque.status, 'pending'),
                'created_at': saque.data_saque.isoformat(),
                'description': f"Saque via {saque.metodo_pagamento}"
            })
        
        # Ordenar por data
        transactions.sort(key=lambda x: x['created_at'], reverse=True)
        
        return jsonify({
            'success': True,
            'transactions': transactions[:20]  # Últimas 20 transações
        })
        
    except Exception as e:
        logging.error(f"Erro ao buscar histórico de transações: {str(e)}")
        return jsonify({'success': False, 'message': 'Erro interno do servidor'}), 500

@transactions_blueprint.route('/api/withdraw/request', methods=['POST'])
def request_withdrawal():
    """Processa solicitação de saque"""
    if 'steam_id' not in session:
        return jsonify({'success': False, 'message': 'Usuário não autenticado'}), 401
    
    try:
        data = request.get_json()
        amount = data.get('amount')
        method = data.get('method')
        
        if not amount or not method:
            return jsonify({'success': False, 'message': 'Dados incompletos'}), 400
        
        if amount <= 0:
            return jsonify({'success': False, 'message': 'Valor inválido'}), 400
        
        user_steam_id = session['steam_id']
        
        # Verificar saldo disponível
        available_balance = trade_hold_service.get_user_available_balance(user_steam_id)
        
        if amount > available_balance:
            return jsonify({
                'success': False, 
                'message': f'Saldo insuficiente. Disponível: R$ {available_balance:.2f}'
            }), 400
        
        # Criar registro de saque
        saque = Saque(
            steamid=user_steam_id,
            valor=amount,
            status='pendente'
        )
        
        db.session.add(saque)
        db.session.commit()
        
        logging.info(f"Solicitação de saque criada: {saque.id} - R$ {amount} via {method}")
        
        return jsonify({
            'success': True,
            'message': 'Solicitação de saque enviada com sucesso!',
            'withdrawal_id': saque.id
        })
        
    except Exception as e:
        logging.error(f"Erro ao processar saque: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Erro interno do servidor'}), 500
