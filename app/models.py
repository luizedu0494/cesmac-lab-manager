from . import db
from datetime import datetime

membros_grupo = db.Table('membros_grupo',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('grupo_id', db.Integer, db.ForeignKey('grupo.id'), primary_key=True)
)

class User(db.Model):
    """Modelo de dados para os usuários do sistema."""
    id = db.Column(db.Integer, primary_key=True)
    google_id = db.Column(db.String(30), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False) # Nome vindo do Google
    nome_exibicao = db.Column(db.String(100), nullable=True) # NOVO: Nome customizável pelo usuário
    picture = db.Column(db.String(200), nullable=True)
    role = db.Column(db.String(20), nullable=False, default='Não Autorizado')
    
    agendamentos_atribuidos = db.relationship('Agendamento', foreign_keys='Agendamento.user_id', backref='atribuido_para', lazy=True)
    avisos = db.relationship('Aviso', backref='autor', lazy=True)
    grupos = db.relationship('Grupo', secondary=membros_grupo, lazy='subquery',
        backref=db.backref('membros', lazy=True))
    agendamentos_criados = db.relationship('Agendamento', foreign_keys='Agendamento.solicitante_id', backref='criador', lazy=True)

    # Propriedade para retornar o nome de exibição ou o nome padrão
    @property
    def display_name(self):
        return self.nome_exibicao or self.name

    def __repr__(self):
        return f"User('{self.name}', '{self.email}', '{self.role}')"

class Grupo(db.Model):
    """Modelo de dados para os grupos/equipes de técnicos."""
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), unique=True, nullable=False)
    
    agendamentos = db.relationship('Agendamento', backref='grupo_atribuido', lazy=True)

    def __repr__(self):
        return f"Grupo('{self.nome}')"

class Agendamento(db.Model):
    """Modelo de dados para os agendamentos de laboratório."""
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(120), nullable=False)
    data = db.Column(db.Date, nullable=False)
    horario_bloco = db.Column(db.String(30), nullable=False)
    laboratorio_id = db.Column(db.String(50), nullable=False)
    laboratorio_nome = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Pendente')
    timestamp_criacao = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    solicitante_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    grupo_id = db.Column(db.Integer, db.ForeignKey('grupo.id'), nullable=True)

    def __repr__(self):
        return f"Agendamento('{self.titulo}', '{self.data.strftime('%d/%m/%Y')}', '{self.status}')"

class Recesso(db.Model):
    """Modelo de dados para os períodos de recesso."""
    id = db.Column(db.Integer, primary_key=True)
    motivo = db.Column(db.String(150), nullable=False)
    data_inicio = db.Column(db.Date, nullable=False)
    data_fim = db.Column(db.Date, nullable=False)

    def __repr__(self):
        return f"Recesso('{self.motivo}', de '{self.data_inicio.strftime('%d/%m/%Y')}' a '{self.data_fim.strftime('%d/%m/%Y')}')"

class Aviso(db.Model):
    """Modelo de dados para os avisos e comunicados."""
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(120), nullable=False)
    conteudo = db.Column(db.Text, nullable=False)
    timestamp_criacao = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Aviso('{self.titulo}', '{self.timestamp_criacao.strftime('%d/%m/%Y')}')"