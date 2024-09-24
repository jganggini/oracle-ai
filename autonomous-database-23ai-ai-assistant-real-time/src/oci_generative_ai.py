import os
import oracledb
from langchain_community.embeddings.oci_generative_ai import OCIGenAIEmbeddings
from langchain_community.chat_models.oci_generative_ai import ChatOCIGenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.vectorstores import OracleVS
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from dotenv import load_dotenv

# Cargar variables de entorno desde un archivo .env
load_dotenv()

def get_db_connection():
    """Establece una conexión con la base de datos Autonomous Database 23AI."""
    connection = oracledb.connect(
        user            = os.getenv('CON_DEV_USER_NAME'),
        password        = os.getenv('CON_DEV_PASSWORD'),
        dsn             = os.getenv('CON_DEV_SERVICE_NAME'),
        config_dir      = os.getenv('CON_WALLET_LOCATION'),
        wallet_location = os.getenv('CON_WALLET_LOCATION'),
        wallet_password = os.getenv('CON_WALLET_PASSWORD')
    )
    return connection

def fetch_access_cases(connection):
    """Ejecuta una consulta SQL para obtener industrias, perfiles y casos de uso."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT industry, profile, case_name FROM access_cases")
        return cursor.fetchall()

def initialize_embeddings():
    """Inicializa un objeto para embeddings de Oracle Cloud Generative AI."""
    emb_model_id     = os.getenv('EMB_MODEL_ID')
    service_endpoint = os.getenv('SERVICE_ENDPOINT')
    compartment_id   = os.getenv('COMPARTMENT_ID')
    
    return OCIGenAIEmbeddings(
        model_id         = emb_model_id,
        service_endpoint = service_endpoint,
        compartment_id   = compartment_id
    )

def create_vector_store(connection, embeddings):
    """Crea un objeto VectorStore que usa la conexión a la base de datos y embeddings."""
    return OracleVS(connection, embeddings, "docs")

def create_chain_with_history(rag_chain, msgs):
    """Crea un objeto para manejar el historial de mensajes con la cadena RAG."""
    return RunnableWithMessageHistory(
        rag_chain,
        lambda session_id: msgs,
        input_messages_key   = "input",
        history_messages_key = "history",
        output_messages_key  = "answer"
    )

def initialize_chat_model_call():
    """Configura el modelo de chat con parámetros específicos."""
    chat_model_id    = os.getenv('CHAT_MODEL_ID')
    service_endpoint = os.getenv('SERVICE_ENDPOINT')
    compartment_id   = os.getenv('COMPARTMENT_ID')
    auth_type        = os.getenv('AUTH_TYPE')
    
    return ChatOCIGenAI(
        model_id         = chat_model_id,
        service_endpoint = service_endpoint,
        compartment_id   = compartment_id,
        provider         = "cohere",
        is_stream        = True,
        auth_type        = auth_type,
        model_kwargs={
            "max_tokens": 512,
            "temperature": 0.6,
            "top_p": 0.7,
            "top_k": 20,
            "frequency_penalty": 0
        }
    )

def create_chat_chain_call(llm, retriever):
    """Crea la cadena de chat combinada con recuperación de documentos"""
    contextualize_q_prompt = ChatPromptTemplate.from_messages([
        ("system", "Given a chat history and the latest user question, formulate a standalone question. Do NOT answer the question, just reformulate it if needed and otherwise return it as is."),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{input}"),
    ])
    
    history_aware_retriever = create_history_aware_retriever(llm, retriever, contextualize_q_prompt)
    
    system_prompt = """
    You are an assistant for question-answering tasks. 
    Please use only the following retrieved context fragments to answer the question. 
    If you don't know the answer, just say that you don't know. 
    Always use all the data.
    You are a call center assistant and you must provide retention alternatives only.
    You do not need to show feelings.
    \n\n 
    {context}
    """
    
    qa_prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{input}"),
    ])
    
    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
    return create_retrieval_chain(history_aware_retriever, question_answer_chain)

def initialize_chat_model_chat():
    """Configura el modelo de chat con parámetros específicos"""
    chat_model_id    = os.getenv('CHAT_MODEL_ID')
    service_endpoint = os.getenv('SERVICE_ENDPOINT')
    compartment_id   = os.getenv('COMPARTMENT_ID')
    auth_type        = os.getenv('AUTH_TYPE')
    
    return ChatOCIGenAI(
        model_id         = chat_model_id,
        service_endpoint = service_endpoint,
        compartment_id   = compartment_id,
        provider         = "cohere",
        is_stream        = True,
        auth_type        = auth_type,
        model_kwargs={
            "max_tokens": 1024,
            "temperature": 0.6,
            "top_p": 0.7,
            "top_k": 20,
            "frequency_penalty": 0.8
        }
    )

def create_chat_chain_chat(llm, retriever):
    """Crea la cadena de chat combinada con recuperación de documentos."""
    contextualize_q_prompt = ChatPromptTemplate.from_messages([
        ("system", "Given a chat history and the latest user question, formulate a standalone question. Do NOT answer the question, just reformulate it if needed and otherwise return it as is."),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{input}"),
    ])
    
    history_aware_retriever = create_history_aware_retriever(llm, retriever, contextualize_q_prompt)
    
    system_prompt = """
    You are an assistant for question-answering tasks. 
    Please use only the following retrieved context fragments to answer the question. 
    If you don't know the answer, just say that you don't know. 
    Always use all the data.
    Your name is Aby.
    \n\n 
    {context}
    """
    
    qa_prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{input}"),
    ])
    
    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
    return create_retrieval_chain(history_aware_retriever, question_answer_chain)