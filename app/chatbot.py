import os
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import DocArrayInMemorySearch
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.documents import Document

faq_data = [
    ("Como aprovo ou rejeito um agendamento?", "Vá para a página 'Calendário'. Os agendamentos pendentes aparecerão em amarelo. Clique sobre o evento desejado e, na janela de detalhes que se abrirá, clique no botão verde 'Aprovar' ou no botão vermelho 'Rejeitar'."),
    ("Como crio um agendamento para um grupo?", "Na página 'Calendário', clique em um dia vago. Na janela de 'Novo Agendamento', na seção 'Atribuir para:', selecione a opção 'Grupo' e, no menu de seleção que aparecerá, escolha a equipe desejada."),
    ("Como cadastro um período de recesso?", "Na barra de navegação superior, clique em 'Gerenciar' e depois 'Gerenciar Recessos'. Na nova página, preencha o formulário com o motivo, a data de início e a data de fim e clique em 'Adicionar Recesso'."),
    ("Como solicito o agendamento de uma aula?", "Vá para a página 'Calendário' e clique em um dia disponível. Preencha os detalhes da aula/evento e clique em 'Salvar Agendamento'. Sua solicitação será enviada para o Coordenador."),
    ("Como sei se meu agendamento foi aprovado?", "No calendário, seu agendamento mudará de cor. Verde significa 'Aprovada', amarelo 'Pendente' e vermelho 'Rejeitada'."),
    ("O que é um dia com fundo colorido no calendário?", "Dias com fundo colorido são bloqueados. Laranja significa feriado e cinza significa período de recesso."),
    ("Como crio uma equipe de técnicos?", "Apenas Coordenadores podem criar equipes. Vá para 'Gerenciar' -> 'Gerenciar Grupos'. Use o formulário no topo para criar um novo grupo e, em seguida, adicione técnicos a ele usando o menu de seleção em cada grupo.")
]

documents = [Document(page_content=answer, metadata={'question': question}) for question, answer in faq_data]

knowledge_base = None

def get_knowledge_base():
    """Cria e armazena em cache a base de conhecimento."""
    global knowledge_base
    if knowledge_base is None:
        print("DEBUG: Tentando criar a base de conhecimento pela primeira vez...")
        try:
            api_key = os.getenv('GEMINI_API_KEY')
            if not api_key:
                print("ERRO CRÍTICO: A chave de API do Gemini (GEMINI_API_KEY) não foi encontrada no ambiente.")
                return None
            
            embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=api_key)
            knowledge_base = DocArrayInMemorySearch.from_documents(documents, embeddings)
            print("DEBUG: Base de conhecimento criada com sucesso.")
        except Exception as e:
            print(f"ERRO CRÍTICO ao criar embeddings ou base de conhecimento: {e}")
            return None
    return knowledge_base

def get_faq_answer(question: str) -> str:
    """Função principal que recebe uma pergunta e retorna a resposta da IA."""
    print("DEBUG: Função get_faq_answer foi chamada.")
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        return "Desculpe, o administrador do sistema não configurou a chave de API para o serviço de IA."

    kb = get_knowledge_base()
    if kb is None:
        return "Desculpe, ocorreu um erro interno ao inicializar a base de conhecimento. Por favor, verifique os logs do servidor."

    retriever = kb.as_retriever()
    
    try:
        llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest", temperature=0.3, google_api_key=api_key)
        
        template = """
        Você é um assistente prestativo do sistema de agendamento de laboratórios do CESMAC.
        Sua tarefa é responder à pergunta do usuário da forma mais clara e direta possível, baseando-se exclusivamente no contexto fornecido.
        Se a informação não estiver no contexto, diga educadamente que você não sabe a resposta para aquela pergunta específica. Não invente informações.
        
        Contexto: {context}
        
        Pergunta: {question}
        
        Resposta prestativa:
        """
        prompt = PromptTemplate(template=template, input_variables=["context", "question"])

        rag_chain = (
            {"context": retriever, "question": RunnablePassthrough()}
            | prompt
            | llm
        )
        
        print(f"DEBUG: Invocando a cadeia da IA com a pergunta: '{question}'")
        response = rag_chain.invoke(question)
        print("DEBUG: Resposta recebida da IA com sucesso.")
        return response.content

    except Exception as e:
        print(f"ERRO CRÍTICO ao invocar a cadeia da IA: {e}")
        return "Desculpe, ocorreu um erro de comunicação com o serviço de IA ao processar sua pergunta. Verifique os logs do servidor."