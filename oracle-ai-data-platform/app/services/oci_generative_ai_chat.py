import os

from langchain_community.chat_models import ChatOCIGenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains import create_history_aware_retriever, create_retrieval_chain

from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import PromptTemplate
from langchain_core.prompts.chat import ChatPromptTemplate, SystemMessagePromptTemplate

import components as component
import services.database as database
from dotenv import load_dotenv

# Initialize the environment variables
load_dotenv()

# Initialize the service
db_doc_service = database.DocService()
db_agent_service = database.AgentService()

class GenerativeAIService:
    """
    Servicio para crear una cadena RAG que use:
      - Un retriever "history-aware" (creado con create_history_aware_retriever)
      - Un chain para combinar documentos (StuffDocumentsChain)
      - Un chain final via create_retrieval_chain
      - Manejo de 'chat_history' en cada invocación
    """

    @staticmethod
    def get_llm(user_id, agent_id):
        # Configuración del agente
        df_agents = db_agent_service.get_all_agents_cache(user_id)[lambda df: df["AGENT_ID"] == agent_id]

        # Configuramos el LLM (OCI Generative AI)
        llm = ChatOCIGenAI(
            model_id         = str(df_agents["AGENT_MODEL_NAME"].values[0]),
            service_endpoint = os.getenv("CON_GEN_AI_SERVICE_ENDPOINT"),
            compartment_id   = os.getenv("CON_COMPARTMENT_ID"),
            provider         = str(df_agents["AGENT_MODEL_PROVIDER"].values[0]),
            is_stream        = True,  # streaming de tokens si lo deseas
            auth_type        = os.getenv("CON_GEN_AI_AUTH_TYPE"),
            model_kwargs     = {
                "temperature" : float(df_agents["AGENT_TEMPERATURE"].values[0]),
            }
        )

        return llm

    @staticmethod
    def get_chain(file_id, user_id, agent_id, history, input, input_imagen):
        """
        Crea una cadena RAG para un agente específico, usando un retriever "history-aware"

        """
        # Configuración del agente
        df_agents = db_agent_service.get_all_agents_cache(user_id)[lambda df: df["AGENT_ID"] == agent_id]

        # 
        llm = GenerativeAIService.get_llm(user_id, agent_id)

        # Obtenemos el vector store ya indexado
        vector_store = db_doc_service.get_vector_store()

        # Creamos el retriever base (filtro por file_id)
        context_retriever = vector_store.as_retriever(
            search_type="mmr",
            search_kwargs={
                "k": 10,         # Número de chunks relevantes que se devuelven
                "fetch_k": 20,   # Número de candidatos iniciales desde los cuales aplicar MMR
                "filter": {"file_id": file_id} # Limita la búsqueda al archivo específico
            }
        )

        # 5) Prompt que reformulará la query usando la historia (opcional)
        reformulation_prompt = ChatPromptTemplate.from_messages([
            ("system",  str(df_agents["AGENT_PROMPT_SYSTEM"].values[0])),
            MessagesPlaceholder(variable_name="history"),
            ("human",   "{input}")
        ])

        # 6) Creamos un retriever "history-aware" que en cada llamada, usará la query reformulada + chat_history
        history_aware_retriever = create_history_aware_retriever(
            llm,
            context_retriever,
            reformulation_prompt
        )
        
        question_answer_prompt = None
        if input_imagen:
            question_answer_prompt = ChatPromptTemplate.from_messages(
                [
                    SystemMessagePromptTemplate(
                        prompt=PromptTemplate(
                            template=str(df_agents['AGENT_PROMPT_MESSAGE'].values[0]),
                            input_variables=["context"],
                        )
                    ),
                    MessagesPlaceholder(variable_name="history"),
                    ("human",
                        [
                            {   "type": "text",
                                "text": f"{str(df_agents['AGENT_PROMPT_MESSAGE'].values[0])}"
                            }, {
                                "type": "image_url",
                                "image_url": {"url": "data:image/jpeg;base64,{input_imagen}"},
                                "detail": "high",
                            }
                        ]
                    ),
                    ("human", "{input}")
                ]
            )

        else:
            # Prompt para combinar documentos (StuffDocumentsChain)
            question_answer_prompt = ChatPromptTemplate.from_messages([
                ("system", str(df_agents["AGENT_PROMPT_MESSAGE"].values[0])),
                MessagesPlaceholder(variable_name="history"),
                ("human", "{input}")
            ])

        combine_docs_chain = create_stuff_documents_chain(llm, question_answer_prompt)

        # 8) Creamos la cadena final (RAG)
        chain = create_retrieval_chain(
            retriever           = history_aware_retriever,
            combine_docs_chain  = combine_docs_chain
        )

        if input_imagen:
            result = chain.invoke({
                "history"      : history,
                "input"        : input,
                "input_imagen" : input_imagen
            })
        else:
            result = chain.invoke({
                "input"        : input,
                "history"      : history
            })

        # 9) Devolvemos
        return result
