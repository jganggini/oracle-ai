import time
import json
from datetime import datetime
import streamlit as st
from annotated_text import annotated_text, annotation
from streamlit_float import *

import components as component
import services.database as database
import services as service
import utils as utils

# Crear una instancia del servicio
select_ai_rag_service = service.SelectAIRAGService()
db_select_ai_rag_service = database.SelectAIRAGService()
utl_function_service = utils.FunctionService()

login = component.get_login()
component.get_footer()

# initialize float feature/capability
float_init()

if login:
    # Header and description for the application
    st.header(":material/plagiarism: Select AI RAG")
    st.caption("Select AI with RAG in Oracle Autonomous Database integrates large language models with data retrieval, enabling context-aware text generation and enhancing SQL workflows with accurate, AI-driven insights.")

    username     = st.session_state["username"]
    language     = st.session_state["language"]
    user_id      = st.session_state["user_id"]
    profile_name = select_ai_rag_service.get_profile(user_id)
    index_name   = select_ai_rag_service.get_index_name(user_id)
    df_files     = db_select_ai_rag_service.get_files(index_name)

    if df_files is not None and not df_files.empty:
        with st.expander("See Files"):
            # Configurar los parámetros
            group_by_columns = ["FILE_NAME"]
            fields = {
                "Start Offset"  : "START_OFFSET",
                "End Offset"    : "END_OFFSET",
                "Content"       : "CONTENT",
                "Location"      : "LOCATION_URI",
                "Last Modified" : "LAST_MODIFIED",
                "Content"       : "CONTENT"
            }
            json_tables = utl_function_service.get_tables_json(df_files, group_by_columns, fields)
                        
            st.markdown("**Json Data**")
            st.json(json_tables, expanded=1)

        # Display chat messages from history on app rerun
        for message in st.session_state["chat-select-ai-rag"]:
            if message["role"] == "ai":
                with st.chat_message(message["role"], avatar="images/llm_aix.svg"):
                    # Render each section of the stored response
                    annotated_text(annotation("Narrate", message["narrate_time"], background="#484c54", color="#ffffff"))
                    st.markdown(message["narrate"])
            else:
                with st.chat_message(message["role"], avatar=":material/psychology:"):
                    st.markdown(message["content"])

        # React to user input
        if prompt := st.chat_input("What is up?"):
            # Display user message in chat message container
            st.chat_message("human", avatar=":material/psychology:").markdown(prompt)
            
            # Add user message to chat history
            st.session_state["chat-select-ai-rag"].append({"role": "human", "content": prompt})

            # Create placeholders for progressive updates
            assistant_message = st.chat_message("ai", avatar="images/llm_aix.svg")
            placeholder = assistant_message.empty()

            try:
                # Build response with consistent formatting
                with placeholder.container():
                    # Variables
                    start_time   = time.time()
                    profile_name = select_ai_rag_service.get_profile(user_id)
                    action       = 'narrate'
                    narrate = db_select_ai_rag_service.get_chat(
                        prompt,
                        profile_name,
                        action,
                        language
                    )
                    narrate_time = f"{(time.time() - start_time) * 1000:.2f} ms"
                    annotated_text(annotation("Narrate", narrate_time, background="#484c54", color="#ffffff"))
                    
                    if "NNN" not in narrate:
                        # narrate
                        st.markdown(narrate)
                    else:
                        # narrate
                        narrate      = st.session_state["language-message"]
                        narrate_time = narrate_time

                        st.markdown(narrate)
                        
                    # Add assistant response to chat history with structured data
                    st.session_state["chat-select-ai-rag"].append({
                        "role"         : "ai",
                        "narrate"      : narrate,
                        "narrate_time" : narrate_time
                    })

            except Exception as e:
                placeholder.error(f"An error occurred: {e}")
        
        # Chat Buttons
        con1 = st.container()
        con2 = st.container()

        with con1:
            float_parent("background-color: var(--default-backgroundColor); margin-left:0.5rem; bottom:7rem; padding-top:1rem; ")
            
            chat = st.session_state["chat-select-ai-rag"]

            st.download_button(
                label="Save",
                icon=":material/download:",
                data=json.dumps(chat, indent=4),
                file_name=f"chat_history_{datetime.now().strftime('%H%M%S%f')}.json",
                mime="text/plain",
                disabled = (False if chat else True)
            )

        with con2:
            float_parent("background-color: var(--default-backgroundColor); margin-left:7rem; bottom:7rem; padding-top:1rem; ")
            
            if st.button("Clear", icon=":material/delete:"):
                st.session_state["chat-select-ai-rag"] = []
                st.rerun()
    
    else:
        st.info("Upload file for this module.", icon=":material/info:")