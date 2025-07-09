import time
import base64
import json
from datetime import datetime
import streamlit as st
from streamlit_float import *

from annotated_text import annotated_text, annotation
from langchain_community.chat_message_histories import StreamlitChatMessageHistory

import components as component
import services.database as database
import services as service
import utils as utils

# Initialize the service
db_doc_service = database.DocService()
db_file_service  = database.FileService()
db_agent_service = database.AgentService()
generative_service = service.GenerativeAIService()
utl_function_service = utils.FunctionService()

from dotenv import load_dotenv
load_dotenv()

login = component.get_login()
component.get_footer()

# initialize float feature/capability
float_init()

if login:
    # Header y descripción
    st.header(":material/network_intelligence: Vector Database")
    st.caption("AI Vector Search enables semantic and value-based searches on business data, enhancing LLM performance and RAG use cases securely and efficiently.")

    username     = st.session_state["username"]
    language     = st.session_state["language"]
    user_id      = st.session_state["user_id"]
    chat_save    = st.session_state["chat-save"]
    df_files     = db_file_service.get_all_files_cache(user_id)[lambda df: df["MODULE_VECTOR_STORE"] == 1]
    df_agents    = db_agent_service.get_all_agents_cache(user_id)[lambda df: df["AGENT_TYPE"] == "Chat"]

    # Aseguramos que el session_id se inicialice una sola vez
    if "chat_session_id" not in st.session_state:
        st.session_state["chat_session_id"] = f"{username}-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"

    chat_session_id               = st.session_state["chat_session_id"]
    chat_human_prompt_input       = "" # Input del mensaje del usuario
    chat_human_prompt_image_input = "" # Input de la imagen del usuario
    chat_ai_answer                = "" # Respuesta generada por la IA
    chat_tokens_rate_answer       = "" # Tasa de tokens por segundo
    chat_tokens                   = 0
    chat_ux_history               = StreamlitChatMessageHistory(key="ux-history")
    chat_history                  = st.session_state["chat-history"]

    @st.dialog("Select Objects")
    def dialog_object():
        
        # Opciones de modelos
        agent_options = df_agents["AGENT_ID"].tolist()
        
        # Determinar el índice predeterminado
        agent_index = agent_options.index(st.session_state["chat-agent"]) if st.session_state["chat-agent"] in agent_options else 0
        
        # Selectbox para modelos
        selected_agent_id = st.selectbox(
            "Which agent would you like to see?",
            options=agent_options,
            format_func=lambda agent_id: f"{df_agents.loc[df_agents['AGENT_ID'] == agent_id, 'AGENT_NAME'].values[0]}",
            index=agent_index,
            placeholder="Select an Agent..."
        )

        if selected_agent_id:

            # 
            selected_anget_multimodal = True if df_agents[df_agents["AGENT_ID"].isin([selected_agent_id])]['AGENT_MODEL_TYPE'].values[0] == 'vlm' else False
                        
            # Multiselect para objetos limitados a los módulos seleccionados
            selected_objects_id = st.multiselect(
                "Which objects would you like to see?",
                options=df_files["FILE_ID"].tolist(),
                format_func=lambda file_id: df_files.loc[df_files["FILE_ID"] == file_id, "FILE_SRC_FILE_NAME"].values[0].rsplit("/", 1)[-1],
                default=st.session_state["chat-objects"],
                placeholder="Select an object..."
            )

            # Mostrar detalles solo de los archivos seleccionados
            with st.expander(":material/files: File Descriptions"):
                df_selected = df_files[df_files["FILE_ID"].isin(selected_objects_id)].copy()
                for idx, (_, row) in enumerate(df_selected.iterrows()):
                    name = row["FILE_SRC_FILE_NAME"].rsplit("/", 1)[-1]
                    description = row["FILE_DESCRIPTION"]
                    owner = row["USER_USERNAME"]

                    st.markdown(f"""
                    **Name:** `{name}`  
                    **Description:** `{description}`  
                    **Owner:** `{owner}`
                    """)

                    # Solo muestra la línea si no es el último
                    if idx < len(df_selected) - 1:
                        st.markdown("***")
            

            if st.button("Save", disabled=(not selected_objects_id)):
                chat_ux_history.clear()
                st.session_state["chat-tokens"]     = 0
                st.session_state["chat-save"]       = []
                st.session_state["chat-agent"]      = selected_agent_id
                st.session_state["chat-multimodal"] = selected_anget_multimodal
                st.session_state["chat-objects"]    = selected_objects_id
                st.rerun()
        
        else:
            st.session_state["chat-agent"]   = 0
            st.session_state["chat-objects"] = []
            st.info("Please select at least one module.")
        

    @st.dialog("Upload Image")
    def dialog_image():
        uploaded_file = st.file_uploader(
            "Choose a File",
            type=["jpg", "jpeg", "png"],
            help="Limit 200MB",
            accept_multiple_files=False
        )

        # Si se selecciona un archivo nuevo, mostrarlo y habilitar el botón "Upload"
        if uploaded_file:
            st.image(uploaded_file, use_container_width=True)
            if st.button("Upload"):
                st.session_state["chat-image"] = uploaded_file.read()
                st.success("File uploaded successfully!")
                st.rerun()

        # Si ya hay un archivo en la sesión, mostrarlo y habilitar el botón "Delete"
        elif "chat-image" in st.session_state and st.session_state["chat-image"]:
            st.image(st.session_state["chat-image"], use_container_width=True)
            if st.button("Delete"):
                st.session_state["chat-image"] = None
                st.success("Image deleted successfully!")
                st.rerun()


    if not df_files.empty:
        df_agent = df_agents[df_agents["AGENT_ID"] == st.session_state["chat-agent"]]

        if not df_agent.empty:
            agent_name = df_agent["AGENT_NAME"].values[0]
            model_name = df_agent["AGENT_MODEL_NAME"].values[0]

            with st.expander(f"[{agent_name}]/[{model_name}] "):
                
                # Seleccionar columnas específicas
                selected_columns = [
                    "AGENT_MODEL_NAME",
                    "AGENT_MODEL_PROVIDER",
                    "AGENT_MAX_OUT_TOKENS",
                    "AGENT_TEMPERATURE",
                    "AGENT_TOP_P",
                    "AGENT_TOP_K",
                    "AGENT_FREQUENCY_PENALTY",
                    "AGENT_PRESENCE_PENALTY",
                    "AGENT_PROMPT_SYSTEM",
                    "AGENT_PROMPT_MESSAGE"
                ]

                # Filtrar y renombrar columnas
                df_filtered = df_agent[selected_columns].rename(
                    columns=lambda col: col.replace("AGENT_", "")
                )

                # Convertir el DataFrame a un diccionario (orientado a registros)
                json_agent = df_filtered.to_dict(orient="records")

                # Mostrar JSON
                st.markdown("**Parameters**")
                st.json(json_agent[0], expanded=True)
            
        
        # Renderizamos el historial previo para UI (sin afectar la memoria interna)
        # Recuerda que chat_ux_history.messages contiene 6 "slots" por cada interacción en tu código
        for i in range(0, len(chat_ux_history.messages), 6):

            # HumanMessage
            chat_human_prompt_message       = chat_ux_history.messages[i].content
            chat_human_prompt_image_message = chat_ux_history.messages[i+1].content
            # AI message
            chat_ai_answer_message    = chat_ux_history.messages[i+2].content            
            chat_tokens_rate_message  = chat_ux_history.messages[i+3].content
            chat_chat_tokens_message  = chat_ux_history.messages[i+4].content
            chat_total_tokens_message = chat_ux_history.messages[i+5].content

            with st.chat_message("human", avatar=":material/psychology:"):
                st.markdown(chat_human_prompt_message)

                if chat_human_prompt_image_message != "":
                    # Convertir la cadena a bytes (si se guardó en str)
                    image_bytes = base64.b64decode(chat_human_prompt_image_message)
                    st.image(image_bytes, use_container_width=True)

            with st.chat_message("ai", avatar="images/llm_meta.svg"):
                st.markdown(chat_ai_answer_message)
                annotated_text(
                    annotation("Rate", chat_tokens_rate_message, background="#484c54", color="#ffffff"),
                    "   ",
                    annotation("Tokens", f"{chat_chat_tokens_message} to {chat_total_tokens_message}", background="#484c54", color="#ffffff")
                )
                st.markdown("\n\n")

        # Manejo del input del usuario
        chat_human_prompt_input = st.chat_input("Type your message here...", disabled=(not st.session_state["chat-objects"]))

        if not st.session_state["chat-objects"]:
            st.info("Please select at least one object to start the chat.")

        if chat_human_prompt_input:
            st.chat_message("human", avatar=":material/psychology:").write(chat_human_prompt_input)
            chat_human_prompt_image_input = None

            # Si había imagen en session_state["chat-image"], la anexamos
            if "chat-image" in st.session_state and st.session_state["chat-image"]:
                chat_human_prompt_image_input = st.session_state["chat-image"]
                
                col1, col2 = st.columns([0.08, 0.92])
                with col1:
                    st.empty()                
                with col2:
                    st.image(chat_human_prompt_image_input, use_container_width=True)                

            # Convertir la lista de (human, ai) a ChatMessages
            messages_for_langchain = utl_function_service.build_langchain_messages_from_qa(chat_history)
            
            # 
            if chat_human_prompt_image_input:
                chat_human_prompt_image_input = utl_function_service.encode_bytes_to_base64(st.session_state["chat-image"])
            else:
                chat_human_prompt_image_input = ""
            
            start_time = time.time()

            # Obtenemos la Retrieval Chain + modelo
            chain = generative_service.get_chain(
                file_id      = st.session_state["chat-objects"],
                user_id      = user_id,
                agent_id     = st.session_state["chat-agent"],
                history      = messages_for_langchain,
                input        = chat_human_prompt_input,
                input_imagen = chat_human_prompt_image_input
            )

            #
            llm = generative_service.get_llm(user_id, st.session_state["chat-agent"])

            # Limpiamos la imagen de la sesión una vez usada
            st.session_state["chat-image"] = None            

            elapsed_time = time.time() - start_time

            # 3. Extraemos la respuesta final
            chat_ai_answer = chain["answer"]

            # 4. Calcular tokens (usando la utilidad del llm_model)
            tokens_ids    = llm.get_token_ids(chat_ai_answer)
            answer_tokens = len(tokens_ids)
            token_rate    = answer_tokens / elapsed_time if elapsed_time > 0 else 0.0
            chat_tokens_rate_answer = f"{token_rate:.2f} tokens/s"

            # Muestra la respuesta en la UI
            placeholder = st.empty()
            with placeholder.chat_message("ai", avatar="images/llm_meta.svg"):
                st.markdown(chat_ai_answer)
                
                # También calculamos los tokens de entrada
                input_tokens = len(llm.get_token_ids(chat_human_prompt_input))
                chat_tokens  = input_tokens + answer_tokens
                total_tokens = sum(int(item["chat_tokens"]) for item in st.session_state["chat-save"]) + chat_tokens

                annotated_text(
                    annotation("Rate", chat_tokens_rate_answer, background="#484c54", color="#ffffff"),
                    "   ",
                    annotation("Tokens", f"{str(chat_tokens)} to {str(total_tokens)}", background="#484c54", color="#ffffff")
                )
                st.markdown("\n\n")
                
                # Guardamos en "chat_ux_history" para que aparezca en la interfaz en la próxima iteración
                chat_ux_history.add_user_message(chat_human_prompt_input)
                chat_ux_history.add_ai_message(str(chat_human_prompt_image_input))  # la imagen
                chat_ux_history.add_ai_message(chat_ai_answer)
                chat_ux_history.add_ai_message(chat_tokens_rate_answer)             # rate
                chat_ux_history.add_ai_message(str(chat_tokens))                    # tokens
                chat_ux_history.add_ai_message(str(total_tokens))                   # total_tokens

                # También guardamos la interacción en chat_save
                chat_data = {
                    "prompt"       : chat_human_prompt_input,
                    "answer"       : chat_ai_answer,
                    "token_rate"   : chat_tokens_rate_answer,
                    "chat_tokens"  : chat_tokens,
                    "total_tokens" : total_tokens
                }
                chat_save.append(chat_data)

            # 5) Actualizamos rag_history => agregamos el par (user_input, bot_answer)
            chat_history.append((chat_human_prompt_input, chat_ai_answer))
        
        # Chat Buttons
        action_buttons_container = st.container()
        with action_buttons_container:
            float_parent("margin-left:0.15rem; bottom:7rem; padding-top:1rem;")
        
        cols_dimensions = [0.08, 0.08, 0.08, 0.08, 0.76]
        col1, col2, col3, col4, col5 = action_buttons_container.columns(cols_dimensions)
        
        with col1:
            if st.button(key="objects", label="", help="Objects", icon=":material/deployed_code_update:"):
                dialog_object()

        with col2:
            if st.button(key="clear", label="", help="Clear Chat", icon=":material/delete:", disabled=(not st.session_state["chat-objects"])):
                chat_ux_history.clear()
                st.session_state["chat-agent"]      = 0
                st.session_state["chat-objects"]    = []
                st.session_state["chat-tokens"]     = 0
                st.session_state["chat-save"]       = []
                st.session_state["chat_session_id"] = ""
                st.session_state["chat-history"]    = []
                st.rerun()

        with col3:
            st.session_state["chat-save"] = chat_save
            st.download_button(
                key="Save",
                label="",
                help="Save Chat",
                icon=":material/download:",
                data=json.dumps(chat_save, indent=4),
                file_name=f"chat_history_{datetime.now().strftime('%H%M%S%f')}.json",
                mime="text/plain",
                disabled=(not st.session_state["chat-objects"])
            ) 
        
        with col4:
            # Sólo habilitar si hay objetos y si el modelo es multimodal
            if st.button(key="image", label="", help="Image", icon=":material/image:", disabled=(not (st.session_state["chat-objects"] and st.session_state["chat-multimodal"]))):
                dialog_image()

        with col5:
            st.empty()
        
    else:
        st.info("Upload file for this module.", icon=":material/info:")