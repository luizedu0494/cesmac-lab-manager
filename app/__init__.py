import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
from sqlalchemy import MetaData

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# --- CONFIGURAÇÃO DEFINITIVA PARA O SQLITE E ALEMBIC ---
# Define a convenção de nomes para todas as constraints (regras) do banco de dados
# para evitar erros no SQLite.
naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

# Inicializa o SQLAlchemy com a convenção de nomes
db = SQLAlchemy(metadata=MetaData(naming_convention=naming_convention))
# Inicializa o Migrate já configurado para operar em batch mode (correto para SQLite)
migrate = Migrate(render_as_batch=True)
# -------------------------------------------------------------

oauth = OAuth()

def create_app():
    """Cria e configura uma instância da aplicação Flask."""
    app = Flask(__name__)

    # --- Configurações da Aplicação ---
    app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'a-chave-secreta-padrao-deve-ser-trocada')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # --- Inicialização das Extensões com a App ---
    db.init_app(app)
    # O migrate agora é inicializado aqui, já com a configuração de batch mode
    migrate.init_app(app, db) 
    
    # --- Configuração do OAuth para Login com Google ---
    oauth.init_app(app)
    oauth.register(
        name='google',
        client_id=os.getenv('GOOGLE_CLIENT_ID'),
        client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={
            'scope': 'openid email profile'
        }
    )

    # --- Registro de Blueprints e Rotas ---
    from . import routes, models
    app.register_blueprint(routes.main_bp)

    return app