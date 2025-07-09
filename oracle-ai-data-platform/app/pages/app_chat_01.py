import time
import json
from datetime import datetime
import streamlit as st
from graphviz import Digraph
from annotated_text import annotated_text, annotation
from streamlit_float import *

import components as component
import services.database as database
import services as service
import utils as utils

# Crear una instancia del servicio
select_ai_service = service.SelectAIService()
db_select_ai_service = database.SelectAIService()
utl_function_service = utils.FunctionService()

login = component.get_login()
component.get_footer()

# initialize float feature/capability
float_init()

if login:
    # Header and description for the application
    st.header(":material/database_search: Select AI")
    st.caption("This application leverages Retrieval-Augmented Generation (RAG) with Oracle 23ai and Deepseek-R1 to retrieve relevant information from a vector database and generate accurate responses using LLMs.")
  
    username     = st.session_state["username"]
    language     = st.session_state["language"]
    user_id      = st.session_state["user_id"]
    chat_save    = st.session_state["chat-select-ai"]
    profile_name = select_ai_service.get_profile(user_id)
    df_tables    = db_select_ai_service.get_tables_cache(user_id)

    if not df_tables.empty:
        with st.expander("See Tables"):
            # Configurar los parámetros
            group_by_columns = ["OWNER", "TABLE_NAME"]
            fields = {
                "column_name" : "COLUMN_NAME",
                "data_type"   : "DATA_TYPE",
                "comments"    : "COMMENTS"
            }
            json_tables = utl_function_service.get_tables_json(df_tables, group_by_columns, fields)

            # Generar el gráfico
            dot_tables = utl_function_service.get_tables_dot(json_tables)

            # Guardar y renderizar el gráfico
            dot_name = f"images/{username}/sel_ai_tables"
            dot_tables.render(dot_name, format="png", cleanup=True)

            # Visualizar el gráfico en Streamlit
            st.markdown("**Tables**")
            st.image(f"{dot_name}.png")
            
            st.markdown("**Json Data**")
            st.json(json_tables, expanded=1)

        # Display chat messages from history on app rerun
        for message in st.session_state["chat-select-ai"]:
            if message["role"] == "ai":
                with st.chat_message(message["role"], avatar="images/llm_aix.svg"):
                    # Render each section of the stored response
                    annotated_text(annotation("Narrate", message["narrate_time"], background="#484c54", color="#ffffff"))
                    st.markdown(message["narrate"])

                    if message.get("showsql"):
                        annotated_text(annotation("ShowSQL", message["showsql_time"], background="#484c54", color="#ffffff"))
                        st.code(message["showsql"], language="plsql")

                        annotated_text(annotation("ExplainSQL", message["explainsql_time"], background="#484c54", color="#ffffff"))
                        st.markdown(message["explainsql"])
            else:
                with st.chat_message(message["role"], avatar=":material/psychology:"):
                    st.markdown(message["content"])
            st.markdown("\n\n")

        # React to user input
        if prompt := st.chat_input("What is up?"):
            # Display user message in chat message container
            st.chat_message("human", avatar=":material/psychology:").markdown(prompt)
            
            # Add user message to chat history
            st.session_state["chat-select-ai"].append({"role": "human", "content": prompt})

            # Create placeholders for progressive updates
            assistant_message = st.chat_message("ai", avatar="images/llm_aix.svg")
            placeholder = assistant_message.empty()

            # Build response with consistent formatting
            with placeholder.container():
                # Fetch narrate with timing
                start_time = time.time()
                action     = 'narrate'
                narrate = db_select_ai_service.get_chat(
                    prompt,
                    profile_name,
                    action,
                    language
                )
                # narrate
                narrate_time = f"{(time.time() - start_time) * 1000:.2f} ms"
                annotated_text(annotation("Narrate", narrate_time, background="#484c54", color="#ffffff"))
                
                if "NNN" not in narrate:
                    # narrate
                    st.markdown(narrate)
                    # showsql
                    start_time = time.time()
                    action     = 'showsql'
                    showsql    = db_select_ai_service.get_chat(
                        prompt,
                        profile_name,
                        action,
                        language
                    )
                    showsql_time = f"{(time.time() - start_time) * 1000:.2f} ms"
                    annotated_text(annotation("ShowSQL", showsql_time, background="#484c54", color="#ffffff"))
                    st.code(showsql, language="plsql")
                    
                    # explainsql
                    start_time = time.time()
                    prompt     = showsql
                    action     = 'explainsql'
                    explainsql = db_select_ai_service.get_chat(
                        prompt,
                        profile_name,
                        action,
                        language
                    )
                    explainsql_time = f"{(time.time() - start_time) * 1000:.2f} ms"
                    annotated_text(annotation("ExplainSQL", explainsql_time, background="#484c54", color="#ffffff"))
                    st.markdown(explainsql)
                
                else:
                    # narrate
                    narrate         =  st.session_state["language-message"]
                    narrate_time    = narrate_time
                    showsql         = ""
                    showsql_time    = "00:00:00"
                    explainsql      = "",
                    explainsql_time = "00:00:00"

                    st.markdown(narrate)
                
                st.markdown("\n\n")
                
                # Guarda el bloque de datos en formato JSON
                chat_data = {
                    "role"            : "ai",
                    "narrate"         : narrate,
                    "narrate_time"    : narrate_time,
                    "showsql"         : showsql,
                    "showsql_time"    : showsql_time,
                    "explainsql"      : explainsql,
                    "explainsql_time" : explainsql_time
                }
                chat_save.append(chat_data)
        

        # Chat Buttons
        action_buttons_container = st.container()
        with action_buttons_container:
            float_parent("margin-left:0.15rem; bottom:7rem; padding-top:1rem;")

        # We set the space between the icons thanks to a share of 100
        cols_dimensions = [0.08, 0.08, 0.76]
        
        col1, col2, col3 = action_buttons_container.columns(cols_dimensions)

        with col1:
            if st.button(key="clear", label="", help="Clear Chat", icon=":material/delete:", disabled=(not st.session_state["chat-select-ai"])):
                st.session_state["chat-select-ai"] = []
                st.rerun()
                
        with col2:
            st.session_state["chat-select-ai"] = chat_save

            st.download_button(
                key="Save",
                label="",
                help="Save Chat",
                icon=":material/download:",
                data=json.dumps(chat_save, indent=4),
                file_name=f"chat_history_{datetime.now().strftime('%H%M%S%f')}.json",
                mime="text/plain",
                disabled=(not st.session_state["chat-select-ai"])
            )

        with col3:
            st.empty()

       
    else:
        st.info("Upload file for this module.", icon=":material/info:")