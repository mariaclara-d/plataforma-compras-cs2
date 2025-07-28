"""
Modelo para Trade Holds - Sistema de proteção de 7 dias
"""
from datetime import datetime, timedelta
from db_config import db

class TradeHold(db.Model):
    __tablename__ = 'trade_holds'
    
    id = db.Column(db.Integer, primary_key=True)
    steam_id = db.Column(db.String(100), nullable=False)  # Steam ID em vez de user_id
    transacao_id = db.Column(db.Integer, db.ForeignKey('transacoes.id'), nullable=False)
    valor = db.Column(db.Float, nullable=False)  # Valor em hold
    item_name = db.Column(db.String(200), nullable=False)  # Nome do item vendido
    status = db.Column(db.String(20), default='active')  # active, completed, reversed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    completed_at = db.Column(db.DateTime, nullable=True)
    reversal_reason = db.Column(db.Text, nullable=True)
    
    # Relacionamento apenas com transacao
    transacao = db.relationship('Transacao', backref='trade_hold', uselist=False)
    
    def __init__(self, steam_id, transacao_id, valor, item_name):
        self.steam_id = steam_id
        self.transacao_id = transacao_id
        self.valor = valor
        self.item_name = item_name
        self.expires_at = datetime.utcnow() + timedelta(days=7)
    
    @property
    def days_remaining(self):
        """Retorna quantos dias restam no hold"""
        if self.status != 'active':
            return 0
        remaining = self.expires_at - datetime.utcnow()
        return max(0, remaining.days)
    
    @property
    def hours_remaining(self):
        """Retorna quantas horas restam no hold"""
        if self.status != 'active':
            return 0
        remaining = self.expires_at - datetime.utcnow()
        return max(0, remaining.total_seconds() / 3600)
    
    @property
    def can_reverse(self):
        """Verifica se ainda pode reverter o trade"""
        return self.status == 'active' and datetime.utcnow() < self.expires_at
    
    @property
    def is_expired(self):
        """Verifica se o hold expirou"""
        return datetime.utcnow() >= self.expires_at
    
    def complete_hold(self):
        """Marca o hold como completado (libera o saldo)"""
        self.status = 'completed'
        self.completed_at = datetime.utcnow()
        db.session.commit()
    
    def reverse_trade(self, reason=None):
        """Reverte o trade (remove o saldo e marca como revertido)"""
        if not self.can_reverse:
            raise ValueError("Trade hold não pode mais ser revertido")
        
        self.status = 'reversed'
        self.completed_at = datetime.utcnow()
        self.reversal_reason = reason
        
        # Remover saldo seria feito aqui se tivéssemos modelo User
        # Por agora apenas marca como revertido
        
        db.session.commit()
    
    @staticmethod
    def get_active_holds_by_user(steam_id):
        """Retorna todos os holds ativos de um usuário"""
        return TradeHold.query.filter_by(
            steam_id=steam_id, 
            status='active'
        ).order_by(TradeHold.created_at.desc()).all()
    
    @staticmethod
    def get_total_hold_amount_by_user(steam_id):
        """Retorna o valor total em hold para um usuário"""
        result = db.session.query(db.func.sum(TradeHold.valor)).filter_by(
            steam_id=steam_id,
            status='active'
        ).scalar()
        return result or 0.0
    
    @staticmethod
    def process_expired_holds():
        """Processa holds expirados (chama periodicamente)"""
        expired_holds = TradeHold.query.filter(
            TradeHold.status == 'active',
            TradeHold.expires_at <= datetime.utcnow()
        ).all()
        
        for hold in expired_holds:
            hold.complete_hold()
        
        return len(expired_holds)
    
    def to_dict(self):
        """Converte para dicionário para JSON"""
        return {
            'id': self.id,
            'steam_id': self.steam_id,
            'transacao_id': self.transacao_id,
            'valor': self.valor,
            'item_name': self.item_name,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat(),
            'days_remaining': self.days_remaining,
            'hours_remaining': round(self.hours_remaining, 1),
            'can_reverse': self.can_reverse,
            'is_expired': self.is_expired
        }
