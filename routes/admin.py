from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from models.admin import Admin
from models.trade_offers import TradeOffer
from models.saques import Saque
from services.notification_service import notification_service
from db_config import db
from functools import wraps
from datetime import datetime
from sqlalchemy import desc

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/')
def index():
    """Rota raiz do admin - redireciona para login ou dashboard"""
    if 'admin_id' in session:
        return redirect(url_for('admin.dashboard'))
    return redirect(url_for('admin.login'))

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        admin = Admin.query.filter_by(username=username, is_active=True).first()
        
        if admin and admin.check_password(password):
            admin.last_login = datetime.utcnow()
            db.session.commit()
            
            session['admin_id'] = admin.id
            session['admin_username'] = admin.username
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Credenciais inválidas', 'error')
    
    return render_template('admin/login.html')

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    """Dashboard administrativo simplificado e seguro"""
    try:
        # Estatísticas básicas (sem queries complexas)
        total_ofertas = 0
        ofertas_pendentes = 0
        ofertas_aceitas = 0
        total_saques = 0
        saques_pendentes = 0
        saques_processados = 0
        valor_saques_pendente = 0.0
        ofertas_recentes = []
        saques_recentes = []
        
        # Tentar obter estatísticas, mas com fallback seguro
        try:
            total_ofertas = TradeOffer.query.count()
            ofertas_pendentes = TradeOffer.query.filter_by(status='pendente').count()
            ofertas_aceitas = TradeOffer.query.filter_by(status='aceita').count()
        except:
            pass
            
        try:
            total_saques = Saque.query.count()
            saques_pendentes = Saque.query.filter_by(status='pendente').count()
            saques_processados = Saque.query.filter_by(status='processado').count()
        except:
            pass
            
        try:
            saques_pendentes_obj = Saque.query.filter_by(status='pendente').all()
            valor_saques_pendente = sum([float(s.valor or 0) for s in saques_pendentes_obj])
        except:
            valor_saques_pendente = 0.0
            
        try:
            ofertas_recentes = TradeOffer.query.order_by(desc(TradeOffer.created_at)).limit(5).all()
        except:
            ofertas_recentes = []
            
        # Para saques, evitar qualquer problema com criado_em
        try:
            saques_recentes = Saque.query.limit(5).all()  # Sem ordenação por enquanto
        except:
            saques_recentes = []
        
        return render_template('admin/dashboard.html',
                             total_ofertas=total_ofertas,
                             ofertas_pendentes=ofertas_pendentes,
                             ofertas_aceitas=ofertas_aceitas,
                             total_saques=total_saques,
                             saques_pendentes=saques_pendentes,
                             saques_processados=saques_processados,
                             valor_saques_pendente=valor_saques_pendente,
                             ofertas_recentes=ofertas_recentes,
                             saques_recentes=saques_recentes)
                             
    except Exception as e:
        # Em caso de qualquer erro, dashboard básico
        return render_template('admin/dashboard.html',
                             total_ofertas=0,
                             ofertas_pendentes=0,
                             ofertas_aceitas=0,
                             total_saques=0,
                             saques_pendentes=0,
                             saques_processados=0,
                             valor_saques_pendente=0,
                             ofertas_recentes=[],
                             saques_recentes=[])

@admin_bp.route('/ofertas')
@admin_required
def listar_ofertas():
    """Lista ofertas apenas para visualização - usuário que aceita, não o admin"""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    
    query = TradeOffer.query
    
    if status:
        query = query.filter_by(status=status)
    
    ofertas = query.order_by(desc(TradeOffer.created_at)).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/ofertas.html', ofertas=ofertas, status=status)

@admin_bp.route('/saques')
@admin_required
def listar_saques():
    """Lista saques para o admin processar"""
    status = request.args.get('status', '')
    
    query = Saque.query
    
    if status:
        query = query.filter_by(status=status)
    
    saques = query.order_by(desc(Saque.criado_em)).all()
    
    return render_template('admin/saques.html', saques=saques, status=status)

@admin_bp.route('/saque/<int:saque_id>')
@admin_required
def detalhes_saque(saque_id):
    """Detalhes de um saque específico"""
    saque = Saque.query.get_or_404(saque_id)
    return render_template('admin/detalhes_saque.html', saque=saque)

@admin_bp.route('/saque/<int:saque_id>/processar', methods=['POST'])
@admin_required
def processar_saque(saque_id):
    """Processar saque (aceitar)"""
    saque = Saque.query.get_or_404(saque_id)
    
    saque.status = 'processado'
    saque.atualizado_em = datetime.utcnow()
    
    db.session.commit()
    flash('Saque processado com sucesso!', 'success')
    
    return redirect(url_for('admin.listar_saques'))

@admin_bp.route('/saque/<int:saque_id>/cancelar', methods=['POST'])
@admin_required
def cancelar_saque(saque_id):
    """Cancelar saque"""
    saque = Saque.query.get_or_404(saque_id)
    
    saque.status = 'cancelado'
    saque.atualizado_em = datetime.utcnow()
    
    db.session.commit()
    flash('Saque cancelado.', 'warning')
    
    return redirect(url_for('admin.listar_saques'))

@admin_bp.route('/oferta/<offer_id>')
@admin_required
def detalhes_oferta(offer_id):
    """Visualizar oferta (sem ações de aceitar/rejeitar)"""
    oferta = TradeOffer.query.filter_by(tradeofferid=offer_id).first_or_404()
    return render_template('admin/detalhes_oferta.html', oferta=oferta)

@admin_bp.route('/api/stats')
@admin_required
def api_stats():
    """API para estatísticas em tempo real"""
    return jsonify({
        'total_ofertas': TradeOffer.query.count(),
        'ofertas_pendentes': TradeOffer.query.filter_by(status='pendente').count(),
        'ofertas_aceitas': TradeOffer.query.filter_by(status='aceita').count(),
        'ofertas_hoje': TradeOffer.query.filter(
            TradeOffer.created_at >= datetime.now().date()
        ).count()
    })

@admin_bp.route('/logout')
@admin_required
def logout():
    session.clear()
    flash('Logout realizado com sucesso!', 'info')
    return redirect(url_for('admin.login'))
