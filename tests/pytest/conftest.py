import pytest
from flask import Flask
from db_config import db
from app import create_app

# --- Configuração de teste ---
class TestConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SECRET_KEY = 'teste'
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False

# ----------- APP FLASK -----------
@pytest.fixture(scope="session")
def app():
    app = create_app()  # sem argumento
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SECRET_KEY'] = 'teste'
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

# Cliente
@pytest.fixture()
def client(app):
    return app.test_client()

# ----------- SESSÃO DO BANCO -----------
@pytest.fixture()
def db_session(app):
    yield db.session
    db.session.rollback()

