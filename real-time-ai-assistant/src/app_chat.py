import os
import ads
import asyncio
import streamlit as st
import pandas as pd
from dotenv import load_dotenv

import oci_generative_ai
import oci_autonomous_database
from langchain_community.chat_message_histories import StreamlitChatMessageHistory

# Load environment variables from a .env file
load_dotenv()

# Initialize database connection and other services
connection  = oci_generative_ai.get_db_connection()
embeddings  = oci_generative_ai.initialize_embeddings()
VectorStore = oci_generative_ai.create_vector_store(connection, embeddings)

def app_chat():
    """Configures the Streamlit user interface for the AI Assistant application"""
    # Header and description for the application
    st.header("_AI Assistant_ :red[Generative AI] :robot_face:")
    st.caption("OCI Speech + OCI Language + Vector Search + :gray[Generative AI]")

    # Sidebar configuration
    with st.sidebar:
        # Display an image in the sidebar
        st.image('https://raw.githubusercontent.com/jganggini/oracle-ai/main/oci.autonomous.db.23ai.generative.ai.speech.to.text/img/oci.components.gif')

        # Explanation section with an expander
        with st.expander("See Explanation"):
            st.write("""
                This chatbot project uses Autonomous Database 23AI 
                to explore and query data within tables. 
                Industries and cases have been incorporated 
                that group tables using embeddings, facilitating 
                the extraction of relevant information.
            """)
        
        # Input field for entering customer code
        customer_code = st.text_input("Customer Code", "000-0001")

        # Botón de búsqueda
        if st.button("Search"):
            # Fetch calls data from the OCI Autonomous Database
            df_audios = oci_autonomous_database.df_select_calls(customer_code)
            st.session_state.filtered_calls_date = df_audios['CALL_DATE'].dt.strftime('%Y-%m-%d %H:%M:%S').tolist()

        # Check if there are filtered calls before showing the multiselect
        if st.session_state['filtered_calls_date']:
            st.session_state.selected_calls_date = st.multiselect(
                "What audios do you want to analyze?", 
                st.session_state.filtered_calls_date
            )
        else:
            st.session_state.selected_calls_date = ""

        # Footer with author information
        st.markdown("""
            <p style="font-size: 12px; text-align: center;">
                Made with ❤️ in Oracle AI · Powered by <a href="https://pe.linkedin.com/in/jganggini" target="_blank">Joel Ganggini</a>
            </p>
        """, unsafe_allow_html=True)

    # Initialize the chat message history in Streamlit
    msgs = StreamlitChatMessageHistory(key="langchain_messages_chat")
    if not msgs.messages:
        msgs.add_ai_message(os.getenv('CON_GEN_MSG'))

    # Configure retriever to search for information in the VectorStore
    retriever = VectorStore.as_retriever(search_kwargs={
        'k': 3, 
        'filter': {'case_name': 'Customer Calls',
                   'customer_code': customer_code,
                   'call_date': st.session_state.selected_calls_date
                   }
    })
    
    # Initialize the large language model for chat
    llm = oci_generative_ai.initialize_chat_model_chat()
    
    # Create the RAG chain and manage the chat message history
    rag_chain = oci_generative_ai.create_chat_chain_chat(llm, retriever)
    chain_with_history = oci_generative_ai.create_chain_with_history(rag_chain, msgs)
    
    # Display chat message history in the Streamlit container
    for msg in msgs.messages:
        st.chat_message(msg.type).write(msg.content)
    
    # Handle user input and chatbot response in the user interface
    if prompt := st.chat_input():
        st.chat_message("human").write(prompt)
        placeholder   = st.empty()
        full_response = ""
        config = {"configurable": {"session_id": "any"}}
        
        # Stream response from the chat chain with history
        for chunk in chain_with_history.stream({"input": prompt}, config):
            if 'answer' in chunk:
                full_response += chunk['answer']
                placeholder.chat_message("ai").write(full_response)
        
        # Display the final response
        placeholder.chat_message("ai").write(full_response)