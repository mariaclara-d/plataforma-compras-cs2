from db_config import db
from datetime import datetime, timezone


class Transacao(db.Model):
    __tablename__ = 'transacoes'

    id = db.Column(db.Integer, primary_key=True)
    steamid = db.Column(db.String(50), nullable=False, index=True)
    # ✅ MUDANÇA: Float → Numeric para precisão financeira
    valor = db.Column(db.Numeric(10, 2), nullable=False)
    metodo = db.Column(db.String(20), nullable=False)  # pix, banco, cripto
    status = db.Column(db.String(20), default='pendente')  # pendente, pago, cancelado
    criado_em = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<Transacao {self.steamid} - R$ {self.valor} - {self.status}>"
    
    @staticmethod
    def get_transacoes_por_status(status=None, steam_id=None):
        """Retorna transações filtradas por status e/ou usuário"""
        query = Transacao.query
        if status:
            query = query.filter_by(status=status)
        if steam_id:
            query = query.filter_by(steamid=steam_id)
        return query.order_by(Transacao.criado_em.desc()).all()
    
    @staticmethod
    def get_total_pago_usuario(steam_id):
        """Retorna total já pago para um usuário"""
        from sqlalchemy import func
        result = db.session.query(func.sum(Transacao.valor)).filter(
            Transacao.steamid == steam_id,
            Transacao.status == 'pago'
        ).scalar()
        return str(result) if result else '0.00'
    
    @staticmethod
    def get_estatisticas():
        """Retorna estatísticas gerais de transações"""
        from sqlalchemy import func
        
        total_pendente = db.session.query(func.sum(Transacao.valor)).filter_by(status='pendente').scalar()
        total_pago = db.session.query(func.sum(Transacao.valor)).filter_by(status='pago').scalar()
        
        return {
            'total_pendente': str(total_pendente) if total_pendente else '0.00',
            'total_pago': str(total_pago) if total_pago else '0.00'
        }
    
    def marcar_como_pago(self):
        """Marca transação como paga"""
        self.status = 'pago'
        db.session.commit()
    
    def cancelar(self):
        """Cancela transação"""
        if self.status == 'pago':
            raise ValueError("Não é possível cancelar transação já paga")
        self.status = 'cancelado'
        db.session.commit()
    
    def to_dict(self):
        """Converte para JSON"""
        return {
            'id': self.id,
            'steamid': self.steamid,
            'valor': str(self.valor) if self.valor else '0.00',
            'metodo': self.metodo,
            'status': self.status,
            'criado_em': self.criado_em.isoformat() if self.criado_em else None
        }
