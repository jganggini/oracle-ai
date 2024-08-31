import os
import oracledb
import streamlit as st

from langchain_community.embeddings.oci_generative_ai import OCIGenAIEmbeddings
from langchain_community.chat_models.oci_generative_ai import ChatOCIGenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.vectorstores import OracleVS
from langchain_community.chat_message_histories import StreamlitChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain.chains import create_history_aware_retriever
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain

from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# Establish a connection to the Autonomous Database 23ai
connection = oracledb.connect(
    user            = os.getenv('CON_DEV_USER_NAME'),
    password        = os.getenv('CON_DEV_PASSWORD'),
    dsn             = os.getenv('CON_DEV_SERVICE_NAME'),
    config_dir      = os.getenv('CON_WALLET_LOCATION'),
    wallet_location = os.getenv('CON_WALLET_LOCATION'),
    wallet_password = os.getenv('CON_WALLET_PASSWORD')
)

# Execute an SQL query to get industries, cases and profiles
with connection.cursor() as cursor:
    cursor.execute("SELECT industry, profile, case_name FROM access_cases")
    access_cases = cursor.fetchall()

# Get a list of unique industries and case names for the user interface
industries = list(set(result[0] for result in access_cases))
profiles   = list(set([result[1] for result in access_cases]))
case_names = [result[2] for result in access_cases]

# Load environment variables required for model configuration and authentication
compartment_id   = os.getenv('COMPARTMENT_ID')
service_endpoint = os.getenv('SERVICE_ENDPOINT')
genai_inference  = os.getenv('GENAI_INFERENCE')
auth_type        = os.getenv('AUTH_TYPE')
emb_model_id     = os.getenv('EMB_MODEL_ID')
chat_model_id    = os.getenv('CHAT_MODEL_ID')

# Initialize an object for Oracle Cloud Generative AI embeddings
embeddings = OCIGenAIEmbeddings(
    model_id=emb_model_id,
    service_endpoint=service_endpoint,
    compartment_id=compartment_id
)

# Main function to set up and run the chatbot
def app_chat():
    # Set up the header and subtitle in the Streamlit user interface
    st.header("_Chatbot with_ :red[ADW 23AI] :sunglasses:")
    st.caption("Vector Search + :gray[Generative AI]")

    # Create a VectorStore object that uses the database connection and embeddings
    VectorStore = OracleVS(connection, embeddings, "docs")

    # Configure the sidebar in the user interface
    with st.sidebar:
        
        # Display an image in the sidebar
        st.image('https://raw.githubusercontent.com/jganggini/oracle-ai/main/autonomous-database-23ai-vectorsearch-chatbot/src/img/chatbot_ai.gif')
        
        # Expand a section to show an explanation of the project
        with st.expander("See Explanation"):
            st.write('''
                Este proyecto de chatbot utiliza Autonomous Database 23AI 
                para explorar y consultar datos dentro de las tablas. 
                Se han incorporado industrias y casos que agrupan 
                las tablas utilizando embeddings, lo que facilita 
                la extracción de información relevante. Además, 
                se ha implementado Generative AI para mejorar 
                la precisión y eficiencia en la búsqueda y consulta 
                de casos específicos dentro del chatbot.
            ''')

        # Allow selection of industry and cases from the user interface
        selected_industry = st.selectbox("What is your industry?", industries)
        filtered_profiles = list(set(result[1] for result in access_cases if result[0] == selected_industry))

        # 
        selected_profiles = st.selectbox("What profiles do you have?", filtered_profiles)
        filtered_case_names = list(set(result[2] for result in access_cases if result[0] == selected_industry and result[1] == selected_profiles))

        # 
        selected_case_names = st.multiselect("What are your case names?", filtered_case_names)

        st.html('''
            <p style="font-size: 12px; text-align: center;">
                Made with ❤️ in Oracle AI · Powered by <a href="https://pe.linkedin.com/in/jganggini" target="_blank">Joel Ganggini</a>
            </p>
        ''')
    
    print("selected_case_names:")
    print(selected_case_names)

    # Initialize the chat message history in Streamlit
    msgs = StreamlitChatMessageHistory(key="langchain_messages")
    if not msgs.messages:
        msgs.add_ai_message("Hola ¿Cúal es su consulta?")

    # Configure the retriever object to search information in the VectorStore
    retriever = VectorStore.as_retriever(search_kwargs={'k': 1000,
                                                        'filter': {
                                                            'case_name': selected_case_names
                                                            }
                                                        })
    
    # Configure the chat model with specific parameters
    llm = ChatOCIGenAI(
        model_id         = chat_model_id,
        service_endpoint = service_endpoint,
        compartment_id   = compartment_id,
        provider         = "cohere",
        is_stream        = True,
        auth_type        = auth_type,
        model_kwargs     = {"max_tokens": 1024, 
                            "temperature": 0.6,
                            "top_p": 0.7,
                            "top_k": 20,
                            "frequency_penalty": 0}
    )

    # Prompt template to contextualize questions based on chat history
    contextualize_q_prompt = ChatPromptTemplate.from_messages([
        ("system", "Given a chat history and the latest user question, formulate a standalone question. Do NOT answer the question, just reformulate it if needed and otherwise return it as is."),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{input}"),
    ])

    # Create a retriever aware of message history
    history_aware_retriever = create_history_aware_retriever(llm, retriever, contextualize_q_prompt)

    # Define the system prompt for question-answering tasks
    system_prompt = """
    You are an assistant for question-answering tasks. 
    Please use only the following retrieved context fragments to answer the question. 
    If you don't know the answer, just say that you don't know. 
    Always use all the data.
    \n\n 
    {context}
    """
    
    # Prompt template for question and answer with the system context
    qa_prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{input}"),
    ])

    # Chain for question answering with retrieved documents
    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
    
    # Chain combining information retrieval with question answering
    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

    # Create an object to handle message history with the RAG chain
    chain_with_history = RunnableWithMessageHistory(
        rag_chain,
        lambda session_id: msgs,
        input_messages_key="input",
        history_messages_key="history",
        output_messages_key="answer"
    )

    # Display the chat message history in the Streamlit user interface
    for msg in msgs.messages:
        st.chat_message(msg.type).write(msg.content)

    # Handle user input and chatbot response in the user interface
    if prompt := st.chat_input():
        st.chat_message("human").write(prompt)
        placeholder   = st.empty()
        full_response = ""
        config = {"configurable": {"session_id": "any"}}
        
        # Process the input and generate responses in real-time
        for chunk in chain_with_history.stream({"input": prompt}, config):
            if 'answer' in chunk:
                full_response += chunk['answer']
                placeholder.chat_message("ai").write(full_response)
                
        # Display the full chatbot response
        placeholder.chat_message("ai").write(full_response)