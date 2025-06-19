import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
from sqlalchemy import MetaData
from flask_mail import Mail # Importa o Flask-Mail

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Define a convenção de nomes para constraints (regras) do banco de dados
naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

db = SQLAlchemy(metadata=MetaData(naming_convention=naming_convention))
migrate = Migrate(render_as_batch=True)
oauth = OAuth()
mail = Mail() # Cria a instância do Mail

def create_app():
    """Cria e configura uma instância da aplicação Flask."""
    app = Flask(__name__)

    # --- Configurações da Aplicação ---
    app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # --- Configurações do Flask-Mail ---
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'true').lower() in ['true', '1', 't']
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_USERNAME')


    # --- Inicialização das Extensões com a App ---
    db.init_app(app)
    migrate.init_app(app, db) 
    oauth.init_app(app)
    mail.init_app(app) # Inicializa o Mail com a app
    
    # --- Configuração do OAuth para Login com Google ---
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