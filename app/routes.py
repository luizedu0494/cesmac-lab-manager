from flask import g, render_template, redirect, url_for, session, flash, Blueprint, jsonify, request, send_file
from . import db, oauth
from .models import User, Agendamento, Recesso, Aviso, Grupo
from .config_data import EMAILS_COORDENADORES, LISTA_LABORATORIOS, BLOCOS_HORARIO
import secrets
from datetime import datetime, timedelta, date
import holidays 
import pandas as pd
import io
from sqlalchemy import or_, func
import json
from . import faq_search

main_bp = Blueprint('main', __name__)

br_holidays = holidays.country_holidays('BR', subdiv='AL', language='pt_BR')

@main_bp.before_request
def load_logged_in_user():
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        g.user = User.query.get(user_id)

@main_bp.route('/')
def index():
    if g.user is None:
        return redirect(url_for('main.login'))
    
    today = date.today()
    dashboard_data = {}

    if g.user.role == 'Coordenador':
        dashboard_data['pendentes_count'] = Agendamento.query.filter_by(status='Pendente').count()
        dashboard_data['aprovados_hoje_count'] = Agendamento.query.filter_by(status='Aprovada', data=today).count()
        dashboard_data['tecnicos_count'] = User.query.filter_by(role='Técnico').count()
        
        utilizacao_labs = db.session.query(
            Agendamento.laboratorio_nome, 
            func.count(Agendamento.id)
        ).group_by(Agendamento.laboratorio_nome).order_by(func.count(Agendamento.id).desc()).limit(7).all()

        dashboard_data['chart_labels'] = json.dumps([item[0] for item in utilizacao_labs])
        dashboard_data['chart_values'] = json.dumps([item[1] for item in utilizacao_labs])

    elif g.user.role == 'Técnico':
        grupo_ids = [grupo.id for grupo in g.user.grupos]
        dashboard_data['proximas_tarefas'] = Agendamento.query.filter(
            Agendamento.status == 'Aprovada',
            Agendamento.data >= today,
            or_(
                Agendamento.user_id == g.user.id,
                Agendamento.grupo_id.in_(grupo_ids)
            )
        ).order_by(Agendamento.data.asc()).limit(5).all()
        
    return render_template('index.html', dashboard=dashboard_data)

@main_bp.route('/login')
def login():
    return render_template('login.html')

@main_bp.route('/auth/google')
def auth_google():
    redirect_uri = url_for('main.auth_callback', _external=True)
    session['nonce'] = secrets.token_urlsafe(16)
    return oauth.google.authorize_redirect(
        redirect_uri, 
        nonce=session['nonce']
    )

@main_bp.route('/auth/callback')
def auth_callback():
    try:
        token = oauth.google.authorize_access_token()
        nonce = session.pop('nonce', None)
        user_info = oauth.google.parse_id_token(token, nonce=nonce)
    except Exception as e:
        print(f"Erro na autenticação: {e}") 
        flash('Ocorreu um erro durante a autenticação. Tente novamente.', 'danger')
        return redirect(url_for('main.login'))

    user_email = user_info.get('email')
    user_google_id = user_info.get('sub')

    user = User.query.filter_by(google_id=user_google_id).first()

    if user:
        user.name = user_info.get('name')
        user.picture = user_info.get('picture')
    else:
        role = 'Não Autorizado'
        if user_email in EMAILS_COORDENADORES:
            role = 'Coordenador'
        
        user = User(
            google_id=user_google_id,
            email=user_email,
            name=user_info.get('name'),
            picture=user_info.get('picture'),
            role=role
        )
        db.session.add(user)
    
    db.session.commit()

    if user.role == 'Não Autorizado':
        flash('Sua conta foi criada, mas aguarda autorização de um coordenador.', 'warning')
        return redirect(url_for('main.login'))

    session.clear()
    session['user_id'] = user.id
    session['user_role'] = user.role 
    session.permanent = True
    flash(f'Login bem-sucedido! Bem-vindo(a), {user.name}.', 'success')
    return redirect(url_for('main.index'))

@main_bp.route('/logout')
def logout():
    session.clear()
    flash('Você saiu do sistema.', 'info')
    return redirect(url_for('main.login'))

@main_bp.route('/perfil', methods=['GET', 'POST'])
def perfil():
    if g.user is None:
        return redirect(url_for('main.login'))

    if request.method == 'POST':
        novo_nome = request.form.get('nome_exibicao')
        if novo_nome and len(novo_nome.strip()) >= 3:
            g.user.nome_exibicao = novo_nome.strip()
            db.session.commit()
            flash('Perfil atualizado com sucesso!', 'success')
            return redirect(url_for('main.perfil'))
        else:
            flash('O nome de exibição precisa ter pelo menos 3 caracteres.', 'warning')

    return render_template('perfil.html')

@main_bp.route('/calendario')
def calendario():
    if g.user is None: 
        return redirect(url_for('main.login'))
    if g.user.role == 'Não Autorizado':
        flash('Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('main.index'))
    
    tecnicos = User.query.filter_by(role='Técnico').all()
    grupos = Grupo.query.all()
    return render_template('calendario.html', 
        laboratorios=LISTA_LABORATORIOS, 
        horarios=BLOCOS_HORARIO, 
        user_role=g.user.role,
        user_id=g.user.id,
        tecnicos=tecnicos,
        grupos=grupos)

@main_bp.route('/minhas-tarefas')
def minhas_tarefas():
    if g.user is None:
        return redirect(url_for('main.login'))
    if g.user.role == 'Não Autorizado':
        flash('Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('main.index'))

    query = Agendamento.query
    if g.user.role != 'Coordenador':
        grupo_ids = [grupo.id for grupo in g.user.grupos]
        query = query.filter(
            or_(
                Agendamento.user_id == g.user.id,
                Agendamento.grupo_id.in_(grupo_ids)
            )
        )

    filtro_texto = request.args.get('filtro_texto')
    if filtro_texto:
        query = query.filter(Agendamento.titulo.ilike(f'%{filtro_texto}%'))

    filtro_status = request.args.get('filtro_status')
    if filtro_status:
        query = query.filter_by(status=filtro_status)

    agendamentos = query.order_by(Agendamento.data.desc()).all()
    return render_template('minhas_tarefas.html', agendamentos=agendamentos)

@main_bp.route('/gerenciar-usuarios', methods=['GET'])
def gerenciar_usuarios():
    if g.user is None or g.user.role != 'Coordenador':
        flash('Acesso não permitido.', 'danger')
        return redirect(url_for('main.index'))
    
    usuarios = User.query.order_by(User.name).all()
    return render_template('gerenciar_usuarios.html', usuarios=usuarios)

@main_bp.route('/usuario/atualizar-perfil/<int:user_id>', methods=['POST'])
def atualizar_perfil(user_id):
    if g.user is None or g.user.role != 'Coordenador':
        flash('Ação não permitida.', 'danger')
        return redirect(url_for('main.index'))
    
    if g.user.id == user_id:
        flash('Você não pode alterar seu próprio perfil aqui.', 'warning')
        return redirect(url_for('main.gerenciar_usuarios'))

    user_para_atualizar = User.query.get_or_404(user_id)
    novo_perfil = request.form.get('novo_perfil')

    if novo_perfil in ['Coordenador', 'Técnico', 'Não Autorizado']:
        user_para_atualizar.role = novo_perfil
        db.session.commit()
        flash(f'O perfil de {user_para_atualizar.display_name} foi atualizado para {novo_perfil}.', 'success')
    else:
        flash('Perfil inválido selecionado.', 'danger')
    
    return redirect(url_for('main.gerenciar_usuarios'))

@main_bp.route('/recessos', methods=['GET', 'POST'])
def gerenciar_recessos():
    if g.user is None or g.user.role != 'Coordenador':
        flash('Acesso não permitido.', 'danger')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        dados = request.form
        motivo = dados.get('motivo')
        data_inicio = datetime.strptime(dados.get('data_inicio'), '%Y-%m-%d').date()
        data_fim = datetime.strptime(dados.get('data_fim'), '%Y-%m-%d').date()

        if data_inicio > data_fim:
            flash('A data de início não pode ser posterior à data de fim.', 'warning')
        else:
            novo = Recesso(motivo=motivo, data_inicio=data_inicio, data_fim=data_fim)
            db.session.add(novo)
            db.session.commit()
            flash('Período de recesso adicionado com sucesso!', 'success')
        return redirect(url_for('main.gerenciar_recessos'))

    recessos = Recesso.query.order_by(Recesso.data_inicio.desc()).all()
    return render_template('recessos.html', recessos=recessos)

@main_bp.route('/recesso/deletar/<int:recesso_id>', methods=['POST'])
def deletar_recesso(recesso_id):
    if g.user is None or g.user.role != 'Coordenador':
        return redirect(url_for('main.index'))
        
    recesso = Recesso.query.get_or_404(recesso_id)
    db.session.delete(recesso)
    db.session.commit()
    flash('Período de recesso excluído.', 'success')
    return redirect(url_for('main.gerenciar_recessos'))

@main_bp.route('/mural', methods=['GET', 'POST'])
def mural_de_avisos():
    if g.user is None:
        return redirect(url_for('main.login'))
    if g.user.role == 'Não Autorizado':
        flash('Você não tem permissão para acessar esta página.', 'danger')
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        if g.user.role != 'Coordenador':
            flash('Ação não permitida.', 'danger')
            return redirect(url_for('main.mural_de_avisos'))
        
        titulo = request.form.get('titulo')
        conteudo = request.form.get('conteudo')
        
        if titulo and conteudo:
            novo_aviso = Aviso(titulo=titulo, conteudo=conteudo, user_id=g.user.id)
            db.session.add(novo_aviso)
            db.session.commit()
            flash('Aviso publicado com sucesso!', 'success')
        else:
            flash('Título e conteúdo são obrigatórios.', 'warning')
        
        return redirect(url_for('main.mural_de_avisos'))

    avisos = Aviso.query.order_by(Aviso.timestamp_criacao.desc()).all()
    return render_template('mural.html', avisos=avisos)

@main_bp.route('/aviso/deletar/<int:aviso_id>', methods=['POST'])
def deletar_aviso(aviso_id):
    if g.user is None or g.user.role != 'Coordenador':
        return redirect(url_for('main.mural_de_avisos'))

    aviso = Aviso.query.get_or_404(aviso_id)
    db.session.delete(aviso)
    db.session.commit()
    flash('Aviso excluído com sucesso.', 'success')
    return redirect(url_for('main.mural_de_avisos'))

@main_bp.route('/ajuda')
def ajuda():
    if g.user is None:
        return redirect(url_for('main.login'))
    return render_template('ajuda.html')

@main_bp.route('/grupos', methods=['GET', 'POST'])
def gerenciar_grupos():
    if g.user is None or g.user.role != 'Coordenador':
        flash('Acesso não permitido.', 'danger')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        nome_grupo = request.form.get('nome_grupo')
        if nome_grupo:
            grupo_existente = Grupo.query.filter_by(nome=nome_grupo).first()
            if not grupo_existente:
                novo = Grupo(nome=nome_grupo)
                db.session.add(novo)
                db.session.commit()
                flash(f'Grupo "{nome_grupo}" criado com sucesso!', 'success')
            else:
                flash('Já existe um grupo com este nome.', 'warning')
        return redirect(url_for('main.gerenciar_grupos'))

    grupos = Grupo.query.order_by(Grupo.nome).all()
    tecnicos = User.query.filter_by(role='Técnico').all()
    
    return render_template('grupos.html', grupos=grupos, tecnicos=tecnicos)

@main_bp.route('/grupo/<int:grupo_id>/adicionar_membro', methods=['POST'])
def adicionar_membro(grupo_id):
    if g.user is None or g.user.role != 'Coordenador': return redirect(url_for('main.index'))
    
    grupo = Grupo.query.get_or_404(grupo_id)
    user_id = request.form.get('user_id')
    if user_id:
        membro = User.query.get(user_id)
        if membro and membro not in grupo.membros:
            grupo.membros.append(membro)
            db.session.commit()
            flash(f'{membro.display_name} adicionado ao grupo {grupo.nome}.', 'success')
        else:
            flash('Este usuário já é membro do grupo.', 'info')
    return redirect(url_for('main.gerenciar_grupos'))

@main_bp.route('/grupo/<int:grupo_id>/remover_membro/<int:user_id>', methods=['POST'])
def remover_membro(grupo_id, user_id):
    if g.user is None or g.user.role != 'Coordenador': return redirect(url_for('main.index'))

    grupo = Grupo.query.get_or_404(grupo_id)
    membro = User.query.get(user_id)
    if membro and membro in grupo.membros:
        grupo.membros.remove(membro)
        db.session.commit()
        flash(f'{membro.display_name} removido do grupo {grupo.nome}.', 'success')
    return redirect(url_for('main.gerenciar_grupos'))

@main_bp.route('/grupo/deletar/<int:grupo_id>', methods=['POST'])
def deletar_grupo(grupo_id):
    if g.user is None or g.user.role != 'Coordenador': return redirect(url_for('main.index'))
    
    grupo = Grupo.query.get_or_404(grupo_id)
    db.session.delete(grupo)
    db.session.commit()
    flash(f'Grupo "{grupo.nome}" excluído com sucesso.', 'success')
    return redirect(url_for('main.gerenciar_grupos'))


@main_bp.route('/agendamento/novo', methods=['POST'])
def novo_agendamento():
    if g.user is None: return jsonify({'error': 'Não autorizado'}), 401
    
    dados = request.form
    data_agendamento = datetime.strptime(dados.get('data'), '%Y-%m-%d').date()

    if data_agendamento in br_holidays:
        nome_feriado = br_holidays.get(data_agendamento)
        return jsonify({'success': False, 'message': f'Não é possível agendar no feriado de {nome_feriado}.'}), 400

    recesso_ativo = Recesso.query.filter(Recesso.data_inicio <= data_agendamento, Recesso.data_fim >= data_agendamento).first()
    if recesso_ativo:
        return jsonify({'success': False, 'message': f'Não é possível agendar durante o período de recesso: {recesso_ativo.motivo}.'}), 400

    lab_id = dados.get('laboratorio')
    lab_nome = next((lab['name'] for lab in LISTA_LABORATORIOS if lab['id'] == lab_id), 'Desconhecido')

    tipo_atribuicao = dados.get('tipo_atribuicao')
    user_id_atribuido = None
    grupo_id_atribuido = None

    if g.user.role == 'Coordenador':
        if tipo_atribuicao == 'user':
            user_id_str = dados.get('atribuido_user_id')
            if user_id_str:
                user_id_atribuido = int(user_id_str)
        elif tipo_atribuicao == 'group':
            grupo_id_str = dados.get('atribuido_grupo_id')
            if grupo_id_str:
                grupo_id_atribuido = int(grupo_id_str)
    else: 
        user_id_atribuido = g.user.id
    
    novo = Agendamento(
        titulo=dados.get('titulo'),
        data=data_agendamento,
        horario_bloco=dados.get('horario'),
        laboratorio_id=lab_id,
        laboratorio_nome=lab_nome,
        status='Pendente',
        user_id=user_id_atribuido,
        grupo_id=grupo_id_atribuido,
        solicitante_id=g.user.id
    )
    db.session.add(novo)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Agendamento solicitado com sucesso!'})

@main_bp.route('/agendamento/editar/<int:agendamento_id>', methods=['POST'])
def editar_agendamento(agendamento_id):
    if g.user is None:
        return jsonify({'success': False, 'message': 'Não autorizado'}), 401
    
    agendamento = Agendamento.query.get_or_404(agendamento_id)

    if agendamento.solicitante_id != g.user.id and g.user.role != 'Coordenador':
        return jsonify({'success': False, 'message': 'Ação não permitida'}), 403

    dados = request.form
    agendamento.titulo = dados.get('titulo')
    agendamento.laboratorio_id = dados.get('laboratorio')
    agendamento.laboratorio_nome = next((lab['name'] for lab in LISTA_LABORATORIOS if lab['id'] == agendamento.laboratorio_id), 'Desconhecido')
    agendamento.horario_bloco = dados.get('horario')
    
    db.session.commit()
    return jsonify({'success': True, 'message': 'Agendamento atualizado com sucesso!'})

@main_bp.route('/agendamento/deletar/<int:agendamento_id>', methods=['POST'])
def deletar_agendamento(agendamento_id):
    if g.user is None:
        return jsonify({'success': False, 'message': 'Não autorizado'}), 401

    agendamento = Agendamento.query.get_or_404(agendamento_id)

    if agendamento.solicitante_id != g.user.id and g.user.role != 'Coordenador':
        return jsonify({'success': False, 'message': 'Ação não permitida'}), 403
    
    db.session.delete(agendamento)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Agendamento excluído com sucesso!'})


@main_bp.route('/importar', methods=['GET', 'POST'])
def importar_agendamentos():
    if g.user is None or g.user.role != 'Coordenador':
        flash('Acesso não permitido.', 'danger')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        if 'planilha' not in request.files:
            flash('Nenhum arquivo selecionado.', 'warning')
            return redirect(request.url)
        
        file = request.files['planilha']
        if file.filename == '':
            flash('Nenhum arquivo selecionado.', 'warning')
            return redirect(request.url)

        if file:
            try:
                df = pd.read_excel(file)
                required_columns = ['TITULO', 'DATA', 'HORARIO', 'LABORATORIO']
                if not all(col in df.columns for col in required_columns):
                    flash(f'A planilha precisa conter as colunas: {", ".join(required_columns)}', 'danger')
                    return redirect(request.url)

                validos = []
                conflitos = []

                for index, row in df.iterrows():
                    try:
                        data_str = str(row['DATA']).split(' ')[0]
                        data_obj = datetime.strptime(data_str, '%Y-%m-%d').date()
                        
                        is_conflict = False
                        if data_obj in br_holidays:
                            row['motivo'] = f"Feriado ({br_holidays.get(data_obj)})"
                            conflitos.append(row.to_dict())
                            is_conflict = True
                        if not is_conflict:
                            recesso_ativo = Recesso.query.filter(Recesso.data_inicio <= data_obj, Recesso.data_fim >= data_obj).first()
                            if recesso_ativo:
                                row['motivo'] = f"Recesso ({recesso_ativo.motivo})"
                                conflitos.append(row.to_dict())
                                is_conflict = True
                        if not is_conflict:
                            lab_nome_original = str(row['LABORATORIO']).strip()
                            horario = str(row['HORARIO']).strip()
                            lab_id = next((lab['id'] for lab in LISTA_LABORATORIOS if lab['name'].strip().lower() == lab_nome_original.lower()), None)
                            
                            if not lab_id:
                                row['motivo'] = "Laboratório não encontrado"
                                conflitos.append(row.to_dict())
                                is_conflict = True
                            else:
                                agendamento_existente = Agendamento.query.filter_by(data=data_obj, horario_bloco=horario, laboratorio_id=lab_id).first()
                                if agendamento_existente:
                                    row['motivo'] = "Horário/Laboratório já ocupado"
                                    conflitos.append(row.to_dict())
                                    is_conflict = True
                        
                        if not is_conflict:
                            validos.append(row.to_dict())
                    except Exception as e:
                        row['motivo'] = f"Erro na linha: {e}"
                        conflitos.append(row.to_dict())

                dados_validos_json = json.dumps(validos, default=str)
                return render_template('preview_importacao.html', validos=validos, conflitos=conflitos, dados_validos_json=dados_validos_json)

            except Exception as e:
                flash(f'Ocorreu um erro ao processar o arquivo: {e}', 'danger')
                return redirect(request.url)

    return render_template('importar_agendamentos.html', laboratorios=LISTA_LABORATORIOS)

@main_bp.route('/importar/confirmar', methods=['POST'])
def confirmar_importacao():
    if g.user is None or g.user.role != 'Coordenador':
        flash('Ação não permitida.', 'danger')
        return redirect(url_for('main.index'))
        
    dados_json = request.form.get('dados_validos')
    if not dados_json:
        flash('Nenhum dado válido para importar.', 'warning')
        return redirect(url_for('main.importar_agendamentos'))

    agendamentos_para_criar = json.loads(dados_json)
    contador = 0
    for item in agendamentos_para_criar:
        lab_nome_original = str(item.get('LABORATORIO')).strip()
        
        lab_id = next((lab['id'] for lab in LISTA_LABORATORIOS if lab['name'].strip().lower() == lab_nome_original.lower()), None)
        
        if lab_id:
            lab_nome_sistema = next((lab['name'] for lab in LISTA_LABORATORIOS if lab['id'] == lab_id), lab_nome_original)
            novo_agendamento = Agendamento(
                titulo=item.get('TITULO'),
                data=datetime.strptime(str(item.get('DATA')).split(' ')[0], '%Y-%m-%d').date(),
                horario_bloco=str(item.get('HORARIO')).strip(),
                laboratorio_id=lab_id,
                laboratorio_nome=lab_nome_sistema,
                status='Pendente',
                solicitante_id=g.user.id
            )
            db.session.add(novo_agendamento)
            contador += 1
    
    if contador > 0:
        db.session.commit()
    flash(f'{contador} agendamentos foram importados e criados com sucesso!', 'success')
    return redirect(url_for('main.calendario'))

@main_bp.route('/download/template')
def download_template():
    if g.user is None or g.user.role != 'Coordenador':
        return redirect(url_for('main.index'))
    return send_file('static/downloads/template_agendamentos.xlsx', as_attachment=True)


@main_bp.route('/api/ajuda-chat', methods=['POST'])
def ajuda_chat():
    if g.user is None:
        return jsonify({'answer': 'Erro: você precisa estar logado para usar o chat.'}), 401
    
    question = request.json.get('question')
    if not question:
        return jsonify({'answer': 'Erro: nenhuma pergunta foi enviada.'}), 400

    answer = faq_search.find_best_faq_answer(question)
    
    return jsonify({'answer': answer})

@main_bp.route('/api/agendamentos')
def api_agendamentos():
    if g.user is None: return jsonify({'error': 'Não autorizado'}), 401

    query = Agendamento.query
    if g.user.role == 'Técnico':
        user = User.query.get(g.user.id)
        grupo_ids = [grupo.id for grupo in user.grupos]
        query = query.filter( or_( Agendamento.user_id == user.id, Agendamento.grupo_id.in_(grupo_ids) ) )

    texto = request.args.get('texto')
    if texto: query = query.filter(Agendamento.titulo.ilike(f'%{texto}%'))
    
    lab_ids = request.args.getlist('lab_ids')
    if lab_ids:
        query = query.filter(Agendamento.laboratorio_id.in_(lab_ids))

    status = request.args.get('status')
    if status: query = query.filter_by(status=status)
    agendamentos = query.order_by(Agendamento.data.asc()).all()

    eventos = []
    for agendamento in agendamentos:
        solicitante_nome = agendamento.criador.display_name if agendamento.criador else 'Sistema'
        atribuido_a = 'N/A'
        if agendamento.atribuido_para: atribuido_a = agendamento.atribuido_para.display_name
        elif agendamento.grupo_atribuido: atribuido_a = f"Grupo: {agendamento.grupo_atribuido.nome}"

        eventos.append({
            'id': agendamento.id,
            'title': agendamento.titulo,
            'start': agendamento.data.isoformat(),
            'extendedProps': {
                'laboratorio_id': agendamento.laboratorio_id,
                'laboratorio_nome': agendamento.laboratorio_nome,
                'horario_bloco': agendamento.horario_bloco,
                'status': agendamento.status,
                'solicitante_id': agendamento.solicitante_id,
                'solicitante': solicitante_nome,
                'atribuido_a': atribuido_a,
                'user_id': agendamento.user_id,
                'grupo_id': agendamento.grupo_id
            },
            'color': '#5cb85c' if agendamento.status == 'Aprovada' else '#f0ad4e' if agendamento.status == 'Pendente' else '#d9534f'
        })
    return jsonify(eventos)

@main_bp.route('/api/feriados')
def api_feriados():
    if g.user is None: return jsonify({'error': 'Não autorizado'}), 401
    ano_atual = datetime.now().year
    feriados_dict = holidays.country_holidays('BR', subdiv='AL', years=[ano_atual, ano_atual + 1], language='pt_BR')
    eventos_feriados = [{'title': nome, 'start': data.isoformat(), 'display': 'background', 'color': '#ff9f89'} for data, nome in feriados_dict.items()]
    return jsonify(eventos_feriados)

@main_bp.route('/api/recessos')
def api_recessos():
    if g.user is None: return jsonify({'error': 'Não autorizado'}), 401
    recessos = Recesso.query.all()
    eventos_recessos = []
    for recesso in recessos:
        delta = recesso.data_fim - recesso.data_inicio
        for i in range(delta.days + 1):
            dia = recesso.data_inicio + timedelta(days=i)
            eventos_recessos.append({'title': recesso.motivo, 'start': dia.isoformat(), 'display': 'background', 'color': '#6c757d'})
    return jsonify(eventos_recessos)

@main_bp.route('/api/novas-notificacoes')
def novas_notificacoes():
    if g.user is None:
        return jsonify([])

    last_check_str = request.args.get('since')
    if not last_check_str:
        return jsonify([])
    
    last_check_dt = datetime.fromisoformat(last_check_str.replace('Z', '+00:00'))

    query = Agendamento.query.filter(Agendamento.timestamp_criacao > last_check_dt)
    notificacoes_finais = []

    if g.user.role == 'Coordenador':
        novas_solicitacoes = query.filter_by(status='Pendente').all()
        for a in novas_solicitacoes:
            notificacoes_finais.append({
                'title': 'Nova Solicitação de Agendamento',
                'body': f'{a.criador.display_name} solicitou "{a.titulo}" para o Lab {a.laboratorio_nome}.'
            })

    elif g.user.role == 'Técnico':
        grupo_ids = [grupo.id for grupo in g.user.grupos]
        novas_atribuicoes = query.filter(
            or_(
                Agendamento.user_id == g.user.id,
                Agendamento.grupo_id.in_(grupo_ids)
            )
        ).all()
        for a in novas_atribuicoes:
            notificacoes_finais.append({
                'title': 'Nova Tarefa Atribuída',
                'body': f'Você foi atribuído à tarefa "{a.titulo}" no Lab {a.laboratorio_nome}.'
            })

    return jsonify(notificacoes_finais)

@main_bp.route('/relatorio/exportar')
def exportar_relatorio():
    if g.user is None or g.user.role != 'Coordenador':
        flash('Ação não permitida.', 'danger')
        return redirect(url_for('main.index'))
    
    query = Agendamento.query.order_by(Agendamento.data.asc())
    texto = request.args.get('texto')
    if texto: query = query.filter(Agendamento.titulo.ilike(f'%{texto}%'))
    
    lab_ids = request.args.getlist('lab_ids')
    if lab_ids:
        query = query.filter(Agendamento.laboratorio_id.in_(lab_ids))
        
    status = request.args.get('status')
    if status: query = query.filter_by(status=status)
    agendamentos_filtrados = query.all()

    if not agendamentos_filtrados:
        flash('Nenhum agendamento encontrado para os filtros selecionados.', 'warning')
        return redirect(url_for('main.calendario'))

    dados_para_planilha = []
    for agendamento in agendamentos_filtrados:
        atribuido_a = 'N/A'
        if agendamento.atribuido_para: atribuido_a = agendamento.atribuido_para.display_name
        elif agendamento.grupo_atribuido: atribuido_a = f"Grupo: {agendamento.grupo_atribuido.nome}"
        dados_para_planilha.append({
            'Data': agendamento.data.strftime('%d/%m/%Y'),
            'Horário': agendamento.horario_bloco,
            'Evento': agendamento.titulo,
            'Laboratório': agendamento.laboratorio_nome,
            'Atribuído a': atribuido_a,
            'Solicitante': agendamento.criador.display_name if agendamento.criador else 'Sistema',
            'Status': agendamento.status
        })
    df = pd.DataFrame(dados_para_planilha)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Agendamentos')
    output.seek(0)
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'relatorio_agendamentos_{datetime.now().strftime("%Y-%m-%d")}.xlsx'
    )