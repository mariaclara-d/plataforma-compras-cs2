from app import create_app
from db_config import db

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        print("Apagando todas as tabelas...")
        db.drop_all()
        print("Criando tabelas vazias...")
        db.create_all()
        print("Banco resetado com sucesso!")
