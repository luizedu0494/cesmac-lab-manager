from thefuzz import process

# Nossa base de conhecimento continua a mesma
faq_data = [
    ("Como aprovo ou rejeito um agendamento?", "Vá para a página 'Calendário'. Os agendamentos pendentes aparecerão em amarelo. Clique sobre o evento desejado e, na janela de detalhes que se abrirá, clique no botão verde 'Aprovar' ou no botão vermelho 'Rejeitar'."),
    ("Como crio um agendamento para um grupo de técnicos?", "Na página 'Calendário', clique em um dia vago. Na janela de 'Novo Agendamento', na seção 'Atribuir para:', selecione a opção 'Grupo' e, no menu de seleção que aparecerá, escolha a equipe desejada."),
    ("Como cadastro um período de recesso ou férias?", "Na barra de navegação superior, clique em 'Gerenciar' e depois 'Gerenciar Recessos'. Na nova página, preencha o formulário com o motivo, a data de início e a data de fim e clique em 'Adicionar Recesso'."),
    ("Como solicito o agendamento de uma aula?", "Vá para a página 'Calendário' e clique em um dia disponível. Preencha os detalhes da aula/evento e clique em 'Salvar Agendamento'. Sua solicitação será enviada para o Coordenador."),
    ("Como sei se meu agendamento foi aprovado?", "No calendário, seu agendamento mudará de cor. Verde significa 'Aprovada', amarelo 'Pendente' e vermelho 'Rejeitada'."),
    ("O que é um dia com fundo colorido no calendário?", "Dias com fundo colorido são bloqueados. Laranja significa feriado e cinza significa período de recesso."),
    ("Como crio uma equipe de técnicos?", "Apenas Coordenadores podem criar equipes. Vá para 'Gerenciar' -> 'Gerenciar Grupos'. Use o formulário no topo para criar um novo grupo e, em seguida, adicione técnicos a ele usando o menu de seleção em cada grupo.")
]

# Prepara os dados para a busca: um dicionário com {pergunta: resposta} e uma lista só com as perguntas
faq_questions_map = {question: answer for question, answer in faq_data}
question_list = list(faq_questions_map.keys())

def find_best_faq_answer(user_question: str) -> str:
    """
    Encontra a pergunta mais parecida no FAQ usando a biblioteca thefuzz e retorna sua resposta.
    """
    if not user_question:
        return "Por favor, digite uma pergunta."

    # Usa a thefuzz para encontrar a melhor correspondência (a pergunta mais parecida)
    # O process.extractOne retorna uma tupla: (pergunta_encontrada, score_de_similaridade)
    best_match = process.extractOne(user_question.lower(), question_list)
    
    if best_match:
        best_question, score = best_match
        
        # Usamos um score de 60 como um bom limiar de confiança.
        # Se a similaridade for maior que 60%, consideramos uma boa resposta.
        if score > 60:
            return faq_questions_map[best_question]

    # Se não encontrar uma correspondência boa o suficiente
    return "Desculpe, não encontrei uma resposta direta para a sua pergunta. Você pode tentar reformulá-la ou consultar os tópicos na página de Ajuda/FAQ."