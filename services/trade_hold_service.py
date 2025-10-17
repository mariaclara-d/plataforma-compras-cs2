"""
Serviço para Trade Holds - Gerenciamento do sistema de proteção
"""
from datetime import datetime, timedelta
from decimal import Decimal
from db_config import db
from models.trade_holds import TradeHold
from models.transacoes import Transacao
from models.saldos import Saldo
from services.notification_service import NotificationService

class TradeHoldService:
    
    @staticmethod
    def create_hold_for_transaction(steam_id, transacao_id, valor, item_name):
        """
        Cria um novo trade hold quando uma venda é realizada
        """
        try:
            # Cria o hold
            hold = TradeHold(
                steam_id=steam_id,
                transacao_id=transacao_id,
                valor=valor,
                item_name=item_name
            )
            
            db.session.add(hold)
            db.session.commit()
            
            # Notifica o usuário sobre o hold
            NotificationService.notify_trade_hold_created(steam_id, hold)
            
            return hold
            
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Erro ao criar trade hold: {str(e)}")
    
    @staticmethod
    def get_user_available_balance(steam_id):
        """
        Calcula o saldo disponível para saque (excluindo valores em hold)
        """
        from models.saldos import Saldo
        
        # Saldo total do usuário
        saldo_atual = Saldo.get_saldo_atual(steam_id) or Decimal('0.00')
        
        # Valor total em hold
        valor_em_hold = TradeHold.get_total_hold_amount_by_user(steam_id)
        
        # Saldo disponível = saldo total - valores em hold
        saldo_disponivel = max(Decimal('0.00'), saldo_atual - valor_em_hold)
        
        return {
            'saldo_total': saldo_atual,
            'valor_em_hold': valor_em_hold,
            'saldo_disponivel': saldo_disponivel
        }
    
    @staticmethod
    def can_withdraw_amount(steam_id, valor_saque):
        """
        Verifica se o usuário pode sacar determinado valor
        """
        balance_info = TradeHoldService.get_user_available_balance(steam_id)
        return balance_info['saldo_disponivel'] >= valor_saque
    
    @staticmethod
    def reverse_trade_hold(hold_id, steam_id, reason=None):
        """
        Permite ao usuário reverter um trade hold
        """
        try:
            hold = TradeHold.query.filter_by(id=hold_id, steam_id=steam_id).first()
            
            if not hold:
                raise ValueError("Trade hold não encontrado")
            
            if not hold.can_reverse:
                raise ValueError("Trade hold não pode mais ser revertido")
            
            # Reverte o hold
            hold.reverse_trade(reason)
            
            # Notifica sobre a reversão
            NotificationService.notify_trade_reversed(steam_id, hold)
            
            return True
            
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Erro ao reverter trade: {str(e)}")
    
    @staticmethod
    def process_expired_holds():
        """
        Processa holds expirados automaticamente
        Deve ser chamado por um job/cron
        """
        try:
            processed_count = TradeHold.process_expired_holds()
            
            # Log da operação
            if processed_count > 0:
                print(f"Trade Holds processados: {processed_count} holds liberados")
            
            return processed_count
            
        except Exception as e:
            print(f"Erro ao processar holds expirados: {str(e)}")
            return 0
    
    @staticmethod
    def get_hold_summary_for_admin():
        """
        Retorna resumo dos holds para administradores
        """
        try:
            active_holds = db.session.query(TradeHold).filter_by(status='active').all()
            completed_holds = db.session.query(TradeHold).filter_by(status='completed').count()
            reversed_holds = db.session.query(TradeHold).filter_by(status='reversed').count()
            
            total_value_in_hold = sum(hold.valor for hold in active_holds)
            
            # Holds expirando hoje
            expiring_today = [
                hold for hold in active_holds
                if hold.expires_at.date() == datetime.now().date()
            ]
            
            return {
                'active_holds_count': len(active_holds),
                'completed_holds_count': completed_holds,
                'reversed_holds_count': reversed_holds,
                'total_value_in_hold': total_value_in_hold,
                'expiring_today_count': len(expiring_today),
                'expiring_today': [hold.to_dict() for hold in expiring_today],
                'recent_active': [hold.to_dict() for hold in active_holds[:10]]
            }
            
        except Exception as e:
            print(f"Erro ao gerar resumo de holds: {str(e)}")
            return None
    
    @staticmethod
    def get_user_hold_info(steam_id):
        """
        Retorna informações completas dos holds de um usuário
        Para exibir no frontend
        """
        try:
            active_holds = TradeHold.get_active_holds_by_user(steam_id)
            balance_info = TradeHoldService.get_user_available_balance(steam_id)
            
            return {
                'balance_info': balance_info,
                'active_holds': [hold.to_dict() for hold in active_holds],
                'has_active_holds': len(active_holds) > 0,
                'next_release_date': min([hold.expires_at for hold in active_holds]) if active_holds else None
            }
            
        except Exception as e:
            print(f"Erro ao obter informações de hold do usuário: {str(e)}")
            return None
