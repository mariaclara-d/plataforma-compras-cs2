from flask_sqlalchemy import SQLAlchemy
import os
from urllib.parse import urlparse

db = SQLAlchemy()

def get_database_url():
    """
    Obtém URL do banco de acordo com o ambiente
    Suporta SQLite (desenvolvimento) e PostgreSQL (produção)
    """
    
    # 1. Heroku PostgreSQL (automático via DATABASE_URL)
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        # Heroku usa postgres:// mas SQLAlchemy precisa postgresql://
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        return database_url
    
    # 2. PostgreSQL manual (VPS, local)
    if all([
        os.getenv('DB_HOST'),
        os.getenv('DB_NAME'),
        os.getenv('DB_USER'),
        os.getenv('DB_PASSWORD')
    ]):
        db_host = os.getenv('DB_HOST')
        db_port = os.getenv('DB_PORT', '5432')
        db_name = os.getenv('DB_NAME')
        db_user = os.getenv('DB_USER')
        db_password = os.getenv('DB_PASSWORD')
        
        return f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
    
    # 3. SQLite (desenvolvimento/fallback)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sqlite_path = os.path.join(current_dir, 'instance', 'users.db')
    return f'sqlite:///{sqlite_path}'

def configure_database(app):
    """
    Configura banco de dados com otimizações específicas
    """
    
    database_url = get_database_url()
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    
    # Configurações gerais
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Configurações específicas para PostgreSQL
    if database_url.startswith('postgresql://'):
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'pool_pre_ping': True,          # Verificar conexões antes de usar
            'pool_recycle': 300,            # Reciclar conexões a cada 5 min
            'pool_timeout': 20,             # Timeout para obter conexão
            'max_overflow': 10,             # Conexões extras além do pool
            'echo': False                   # Log SQL em desenvolvimento
        }
        
        # Log do banco configurado
        parsed_url = urlparse(database_url)
        print(f"🗄️ PostgreSQL configurado: {parsed_url.hostname}:{parsed_url.port}/{parsed_url.path[1:]}")
        
    else:
        # Configurações para SQLite
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
            'echo': app.config.get('DEBUG', False)
        }
        print(f"🗄️ SQLite configurado: {database_url}")
    
    # Inicializar SQLAlchemy
    db.init_app(app)
    
    return database_url