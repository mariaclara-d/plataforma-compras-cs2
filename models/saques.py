from db_config import db
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship


class Saque(db.Model):
    __tablename__ = 'saques'

    id = db.Column(db.Integer, primary_key=True)

    steamid = db.Column(
        db.String(50),
        db.ForeignKey('saldos.steamid'), #Relaciona com a tabela saldos
        nullable=False,
        index=True #performance para buscas

    )
    

    valor = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(20), default='pendente')  # pendente, aprovado, recusado, pago

    criado_em = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    atualizado_em = db.Column(db.DateTime, 
                              default=lambda: datetime.now(timezone.utc), 
                              onupdate=lambda: datetime.now(timezone.utc))



    # Relacionamento com Saldo
    saldo = db.relationship('Saldo', backref='saques')

    def __repr__(self):
        return f"<Saque {self.steamid}: R$ {self.valor:.2f} - {self.status}>"

    # métodos estáticos (consultas gerais)
    @staticmethod
    def get_saques_pendentes(steam_id=None):

        query = Saque.query.filter_by(status='pendente')
        if steam_id:
            query = query.filter_by(steamid=steam_id)
        return query.order_by(Saque.criado_em.desc()).all()
    
    @staticmethod
    def get_total_sacado(steam_id):
        from sqlalchemy import func
        result = db.session.query(func.sum(Saque.valor)).filter(
            Saque.steamid == steam_id,
            Saque.status.in_(['aprovado', 'pago'])
        ).scalar()

        return Decimal(str(result)) if result else Decimal('0.00')
    
    # métodos de instância (ações em saque específico)

    def aprovar(self):

        if self.status != 'pendente':
            raise ValueError(f"Não é possível aprovar saque com status: {self.status}")
        
        self.status = 'aprovado'
        self.atualizado_em = datetime.now(timezone.utc) 
        db.session.commit()

    def rejeitar(self):

            self.status = 'recusado'
            self.atualizado_em = datetime.now(timezone.utc)
            db.session.commit()

    def marcar_como_pago(self):

        if self.status != 'aprovado':
            raise ValueError(f"Não é possível marcar como pago saque com status: {self.status}")
        
        self.status = 'pago'
        self.atualizado_em = datetime.now(timezone.utc)
        db.session.commit()

    def to_dict(self):
        return {
            'id': self.id,
            'steamid': self.steamid,
            'valor': str(self.valor) if self.valor else '0.0',
            'status': self.status,
            'criado_em': self.criado_em.isoformat() if self.criado_em else None,
            'atualizado_em': self.atualizado_em.isoformat() if self.atualizado_em else None
        }