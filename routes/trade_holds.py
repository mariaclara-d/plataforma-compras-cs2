"""
Rotas para gerenciamento de Trade Holds
"""
from flask import Blueprint, request, jsonify, session, render_template
from models.trade_holds import TradeHold
from services.trade_hold_service import TradeHoldService
from flask_wtf.csrf import generate_csrf
import logging

bp = Blueprint('trade_holds', __name__)

def login_required_api(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'steam_id' not in session:
            return jsonify({'erro': 'Usuário não autenticado'}), 401
        return f(*args, **kwargs)
    return decorated

@bp.route('/api/trade-holds/info')
@login_required_api
def get_user_holds_info():
    """
    Retorna informações dos trade holds do usuário atual
    """
    try:
        steam_id = session.get('steam_id')
        hold_info = TradeHoldService.get_user_hold_info(steam_id)
        
        if hold_info is None:
            return jsonify({'erro': 'Erro ao obter informações'}), 500
            
        return jsonify({
            'sucesso': True,
            'data': hold_info
        })
        
    except Exception as e:
        logging.error(f"Erro ao obter holds do usuário: {e}")
        return jsonify({'erro': 'Erro interno'}), 500

@bp.route('/api/trade-holds/reverse/<int:hold_id>', methods=['POST'])
@login_required_api
def reverse_trade_hold(hold_id):
    """
    Permite ao usuário reverter um trade hold
    """
    try:
        steam_id = session.get('steam_id')
        data = request.get_json() or {}
        reason = data.get('reason', 'Solicitação do usuário')
        
        success = TradeHoldService.reverse_trade_hold(hold_id, steam_id, reason)
        
        if success:
            return jsonify({
                'sucesso': True,
                'mensagem': 'Trade revertido com sucesso'
            })
        else:
            return jsonify({'erro': 'Falha ao reverter trade'}), 400
            
    except Exception as e:
        logging.error(f"Erro ao reverter trade hold: {e}")
        return jsonify({'erro': str(e)}), 400

@bp.route('/api/trade-holds/balance')
@login_required_api
def get_balance_info():
    """
    Retorna informações detalhadas de saldo para exibir no frontend
    """
    try:
        steam_id = session.get('steam_id')
        balance_info = TradeHoldService.get_user_available_balance(steam_id)
        
        return jsonify({
            'sucesso': True,
            'balance': balance_info
        })
        
    except Exception as e:
        logging.error(f"Erro ao obter informações de saldo: {e}")
        return jsonify({'erro': 'Erro interno'}), 500

@bp.route('/trade-protection')
@login_required_api
def trade_protection_page():
    """
    Página para visualizar e gerenciar trade holds
    """
    try:
        steam_id = session.get('steam_id')
        
        # Obter informações dos holds
        hold_info = TradeHoldService.get_user_hold_info(steam_id)
        
        return render_template('trade_protection.html', 
                             hold_info=hold_info,
                             csrf_token=generate_csrf())
        
    except Exception as e:
        logging.error(f"Erro ao carregar página de trade protection: {e}")
        return render_template('error.html', 
                             error_message="Erro ao carregar informações de proteção")

# Rotas ADMIN para gerenciar trade holds
@bp.route('/admin/trade-holds')
def admin_trade_holds():
    """
    Página administrativa para monitorar trade holds
    """
    # Verificar se é admin (implementar verificação adequada)
    try:
        summary = TradeHoldService.get_hold_summary_for_admin()
        
        return render_template('admin/trade_holds.html', 
                             summary=summary,
                             csrf_token=generate_csrf())
        
    except Exception as e:
        logging.error(f"Erro ao carregar página admin de trade holds: {e}")
        return render_template('error.html', 
                             error_message="Erro ao carregar painel administrativo")

@bp.route('/admin/api/trade-holds/process-expired', methods=['POST'])
def admin_process_expired():
    """
    Força o processamento de holds expirados (rota admin)
    """
    try:
        processed_count = TradeHoldService.process_expired_holds()
        
        return jsonify({
            'sucesso': True,
            'mensagem': f'{processed_count} holds processados',
            'processed_count': processed_count
        })
        
    except Exception as e:
        logging.error(f"Erro ao processar holds expirados: {e}")
        return jsonify({'erro': 'Erro ao processar holds'}), 500
