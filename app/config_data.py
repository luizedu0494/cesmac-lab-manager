# app/config_data.py

# --- E-MAILS DE TESTE PARA PERFIS DE USUÁRIO ---
# Usados durante o desenvolvimento para simular os diferentes níveis de acesso.
EMAILS_COORDENADORES = [
    'fgojp61@gmail.com'
]

EMAILS_TECNICOS = [
    'dgjheuh@gmail.com'
]


# --- LISTA OFICIAL DE LABORATÓRIOS ---
LISTA_LABORATORIOS = [
    {'id': 'anatomia_1', 'name': 'Anatomia 1', 'tipo': 'anatomia'},
    {'id': 'anatomia_2', 'name': 'Anatomia 2', 'tipo': 'anatomia'},
    {'id': 'anatomia_3', 'name': 'Anatomia 3', 'tipo': 'anatomia'},
    {'id': 'anatomia_4', 'name': 'Anatomia 4', 'tipo': 'anatomia'},
    {'id': 'anatomia_5', 'name': 'Anatomia 5', 'tipo': 'anatomia'},
    {'id': 'anatomia_6', 'name': 'Anatomia 6', 'tipo': 'anatomia'},
    {'id': 'microscopia_1', 'name': 'Microscopia 1', 'tipo': 'microscopia_normal'},
    {'id': 'microscopia_2', 'name': 'Microscopia 2', 'tipo': 'microscopia_normal'},
    {'id': 'microscopia_3', 'name': 'Microscopia 3', 'tipo': 'microscopia_normal'},
    {'id': 'microscopia_4', 'name': 'Microscopia 4', 'tipo': 'microscopia_normal'},
    {'id': 'microscopia_5', 'name': 'Microscopia 5', 'tipo': 'microscopia_normal'},
    {'id': 'microscopia_6_galeria', 'name': 'Microscopia 6 (Galeria)', 'tipo': 'microscopia_galeria'},
    {'id': 'microscopia_7_galeria', 'name': 'Microscopia 7 (Galeria)', 'tipo': 'microscopia_galeria'},
    {'id': 'multidisciplinar_1', 'name': 'Multidisciplinar 1', 'tipo': 'multidisciplinar'},
    {'id': 'multidisciplinar_2', 'name': 'Multidisciplinar 2', 'tipo': 'multidisciplinar'},
    {'id': 'multidisciplinar_3', 'name': 'Multidisciplinar 3', 'tipo': 'multidisciplinar'},
    {'id': 'multidisciplinar_4', 'name': 'Multidisciplinar 4', 'tipo': 'multidisciplinar'},
    {'id': 'habilidade_1_ney_braga', 'name': 'Habilidade 1 (Ney Braga)', 'tipo': 'habilidade_ney_braga'},
    {'id': 'habilidade_2_ney_braga', 'name': 'Habilidade 2 (Ney Braga)', 'tipo': 'habilidade_ney_braga'},
    {'id': 'habilidade_3_ney_braga', 'name': 'Habilidade 3 (Ney Braga)', 'tipo': 'habilidade_ney_braga'},
    {'id': 'habilidades_1_santander', 'name': 'Habilidades 1 (Santander)', 'tipo': 'habilidade_santander'},
    {'id': 'habilidades_2_santander', 'name': 'Habilidades 2 (Santander)', 'tipo': 'habilidade_santander'},
    {'id': 'habilidades_3_santander', 'name': 'Habilidades 3 (Santander)', 'tipo': 'habilidade_santander'},
    {'id': 'habilidades_1_galeria', 'name': 'Habilidades 1 (Galeria)', 'tipo': 'habilidade_galeria'},
    {'id': 'habilidades_2_galeria', 'name': 'Habilidades 2 (Galeria)', 'tipo': 'habilidade_galeria'},
    {'id': 'habilidades_3_galeria', 'name': 'Habilidades 3 (Galeria)', 'tipo': 'habilidade_galeria'},
    {'id': 'farmaceutico', 'name': 'Farmacêutico', 'tipo': 'farmaceutico'},
    {'id': 'tec_dietetica', 'name': 'Tec. Dietética', 'tipo': 'tecdietetica'},
    {'id': 'uda', 'name': 'UDA', 'tipo': 'uda'}
]


# --- BLOCOS DE HORÁRIO PARA AGENDAMENTO ---
BLOCOS_HORARIO = [
    {"value": "07:00-09:10", "label": "07:00 - 09:10", "turno": "Matutino"},
    {"value": "09:30-12:00", "label": "09:30 - 12:00", "turno": "Matutino"},
    {"value": "13:00-15:10", "label": "13:00 - 15:10", "turno": "Vespertino"},
    {"value": "15:30-18:00", "label": "15:30 - 18:00", "turno": "Vespertino"},
    {"value": "18:30-20:10", "label": "18:30 - 20:10", "turno": "Noturno"},
    {"value": "20:30-22:00", "label": "20:30 - 22:00", "turno": "Noturno"},
]