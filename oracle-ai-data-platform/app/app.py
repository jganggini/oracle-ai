import streamlit as st
import streamlit.components.v1 as components
import fitz
import json
from pathlib import Path
from datetime import datetime
import asyncio

import components as component
import services.database as database
import services as service
import utils as utils

# Create service instances
db_module_service             = database.ModuleService()
db_agent_service              = database.AgentService()
bucket_service                = service.BucketService()
select_ai_service             = service.SelectAIService()
select_ai_rag_service         = service.SelectAIRAGService()
document_undestanding_service = service.DocumentUnderstandingService()
speech_service                = service.SpeechService()
document_multimodal           = service.DocumentMultimodalService()
anomaly_engine_service        = service.AnalyzerEngineService()
db_file_service               = database.FileService()
db_doc_service                = database.DocService()
utl_function_service          = utils.FunctionService()
db_user_service               = database.UserService()

language_map = {
    "Spanish"    : "esa",
    "Portuguese" : "ptb",
    "English"    : "gb"
}

map_state = {
    1: "Active",
    2: "Inactive",
    0: "Delete"
}
reverse_map_state = {v: k for k, v in map_state.items()}

st.set_page_config(
    page_title="AI Data Platform | Oracle",
    page_icon="🅾️"
)

component.get_login()
component.get_footer()

# Session state init
if "show_form_app" not in st.session_state:
    st.session_state["show_form_app"] = False
    st.session_state["form_mode_app"] = "create"
    st.session_state["selected_file"] = None
    

if "username" in st.session_state and "user_id" in st.session_state:
    st.header(":material/book_ribbon: Knowledge")
    st.caption("Manage Knowledge")
        
    username = st.session_state["username"]
    user_id = st.session_state["user_id"]
    user_group_id = st.session_state["user_group_id"]
    language = st.session_state["language"]

    df_files = db_file_service.get_all_files_cache(user_id)

    # Variables: Default
    file_src_strategy   = None
    trg_type            = None
    comment_data_editor = None

    # File List
    if not st.session_state["show_form_app"]:
        with st.container(border=True):
            st.badge("List Files")
            
            if df_files.empty:
                st.info("No files found.")
            else:
                df_view = df_files.copy()
                df_view["Status"] = df_view["FILE_STATE"].map(map_state)
                df_view["View"] = False
                df_view["Share"] = False
                df_view["Delete"] = False                

                edited_df = st.data_editor(
                    df_view,
                    use_container_width=True,
                    hide_index=True,
                    num_rows="fixed",
                    column_config={
                        "USER_ID" : None,
                        "MODULE_ID"      : None,
                        "FILE_STATE"     : None,
                        "FILE_SRC_SIZE"  : None,
                        "FILE_SRC_STRATEGY": None,
                        "MODULE_VECTOR_STORE": None,
                        "FILE_TRG_OBJ_NAME": None,
                        "FILE_TRG_TOT_PAGES": None,
                        "FILE_TRG_TOT_CHARACTERS": None,
                        "FILE_TRG_TOT_TIME": None,
                        "FILE_TRG_LANGUAGE": None,
                        "FILE_TRG_PII": None,
                        "FILE_TRG_EXTRACTION": None,
                        "OWNER": None,
                        "FILE_DESCRIPTION": None,
                        "USER_EMAIL": None,
                        "USER_GROUP_ID": None,
                        "USER_ID_OWNER": None,
                        "FILE_ID": st.column_config.Column("ID", disabled=True),
                        "MODULE_NAME": st.column_config.Column("Module", disabled=True),
                        "FILE_SRC_FILE_NAME": st.column_config.LinkColumn("File", display_text=r".*/(.+)$", disabled=True),
                        "USER_USERNAME": st.column_config.Column("Owner", disabled=True),
                        "FILE_USERS": st.column_config.Column("Share", disabled=True),
                        "FILE_DATE": st.column_config.Column("Change", disabled=True),
                        "FILE_VERSION": st.column_config.Column("Ver.", disabled=True),
                        "Status": st.column_config.Column("Status", disabled=True),
                        "Share": st.column_config.CheckboxColumn("Share", help="Check to share file", default=False),
                        "View": st.column_config.CheckboxColumn("View", help="Check to view file details", default=False),
                        "Delete": st.column_config.CheckboxColumn("Delete", help="Check to delete this file", default=False)
                    }
                )

                btn_col1, btn_col2, btn_col3, btn_col4 = st.columns([2, 2.2, 2.2, 3.8])
                
                if btn_col1.button("View", type="secondary", use_container_width=True, icon=":material/table_eye:"):
                    rows_to_edit = edited_df[edited_df["View"] == True]
                    if rows_to_edit.empty:
                        st.warning("Please select at least one file to view.", icon=":material/add_alert:")
                    else:
                        for _, selected_row in rows_to_edit.iterrows():
                            file_id = selected_row["FILE_ID"]
                            data = df_view[df_view["FILE_ID"] == file_id].iloc[0].to_dict()
                            st.session_state.update({
                                "show_form_app": True,
                                "form_mode_app": "view",
                                "selected_file": data
                            })
                            st.rerun()

                if btn_col2.button("Share", type="secondary", use_container_width=True, icon=":material/share:"):
                    rows = edited_df[edited_df["Share"] == True]

                    if rows.empty:
                        st.warning("Please select at least one file to share.", icon=":material/add_alert:")
                    else:
                        for _, selected_row in rows.iterrows():
                            module_id = selected_row["MODULE_ID"]
                            module_name = selected_row.get("MODULE_NAME", f"Module {module_id}")

                            # Validar si el módulo es no compartible
                            if module_id in [0, 1, 2]:
                                st.warning(
                                    f"Cannot share file from **{module_name}**. Sharing is not allowed for these modules.",
                                    icon=":material/block:"
                                )
                                continue

                            # Validar si el usuario es el propietario del archivo
                            if selected_row["USER_ID"] != selected_row["USER_ID_OWNER"]:
                                owner_email = selected_row.get("USER_EMAIL", "unknown@email.com")
                                st.warning(
                                    f"Only the file owner can manage sharing. Please contact: **{owner_email}**",
                                    icon=":material/error:"
                                )
                                continue

                            # Abrir formulario de compartición
                            file_id = selected_row["FILE_ID"]
                            data = df_view[df_view["FILE_ID"] == file_id].iloc[0].to_dict()
                            st.session_state.update({
                                "show_form_app": True,
                                "form_mode_app": "share",
                                "selected_file": data
                            })
                            st.rerun()

                
                if btn_col3.button("Delete", type="secondary", use_container_width=True, icon=":material/delete:"):
                    try:
                        rows_to_edit = edited_df[edited_df["Delete"] == True]
                        if rows_to_edit.empty:
                            st.warning("Please select at least one file to delete.", icon=":material/add_alert:")
                        else:
                            component.get_processing(True)

                            for _, row in rows_to_edit.iterrows():
                                file_id = row["FILE_ID"]
                                file_name = row["FILE_SRC_FILE_NAME"].rsplit("/", 1)[-1]
                                object_name = row["FILE_SRC_FILE_NAME"].split("/o/")[-1]
                                shared_users = row.get("FILE_USERS", 0)

                                if row["OWNER"] == 1:
                                    if shared_users > 0:
                                        st.warning(
                                            f"File '{file_name}' cannot be deleted because it has been shared with {shared_users} user(s).",
                                            icon=":material/block:"
                                        )
                                        continue  # skip deletion
                                    # Eliminar completamente
                                    if bucket_service.delete_object(object_name):
                                        msg = db_file_service.delete_file(file_name, file_id)
                                        component.get_success(msg, icon=":material/database:")
                                else:
                                    # Solo remover acceso
                                    msg = db_file_service.delete_file_user_by_user(file_id, user_id, file_name)
                                    component.get_success(msg, icon=":material/remove_circle:")

                            db_file_service.get_all_files_cache(user_id, force_update=True)

                    except Exception as e:
                        component.get_error(f"[Error] Deleting File:\n{e}")
                    finally:
                        component.get_processing(False)

    # File View
    if st.session_state["show_form_app"]:
        mode = st.session_state["form_mode_app"]

        with st.container(border=True):
            st.badge(
                "Create File" if mode == "create" else "View File" if mode == "view" else "Share File",
                color="green" if mode == "create" else "blue" if mode == "view" else "orange"
            )
            data = st.session_state["selected_file"]

            if mode == "create":
                df_modules = db_module_service.get_modules_cache(user_id, force_update=True)
                df_agents = db_agent_service.get_all_agents_cache(user_id, force_update=True)
                df_agents = df_agents[df_agents["AGENT_TYPE"] == "Extraction"]

                if not df_modules.empty:
                    selected_module_id = st.selectbox(
                        "Which module would you like to start with?",
                        options=df_modules["MODULE_ID"],
                        format_func=lambda module_id: f"{module_id}: {df_modules.loc[df_modules['MODULE_ID'] == module_id, 'MODULE_NAME'].squeeze()}"
                    )

                    selected_agent_id = 0
                    if selected_module_id == 5 and not df_agents.empty:
                        selected_agent_id = st.selectbox(
                            "Which agent would you like to use?",
                            options=df_agents["AGENT_ID"],
                            format_func=lambda agent_id: f"{agent_id}: {df_agents.loc[df_agents['AGENT_ID'] == agent_id, 'AGENT_NAME'].values[0]} ({df_agents.loc[df_agents['AGENT_ID'] == agent_id, 'AGENT_TYPE'].values[0]})"
                        )

                    module_data = df_modules.loc[df_modules["MODULE_ID"] == selected_module_id].iloc[0]
                    selected_module_folder = module_data["MODULE_FOLDER"]
                    selected_src_types = utl_function_service.get_list_to_str(module_data["MODULE_SRC_TYPE"])
                    selected_trg_type = utl_function_service.get_list_to_str(module_data["MODULE_TRG_TYPE"])

                    selected_language_file = st.selectbox(
                        "What is the language of the file?",
                        options=list(language_map.keys()),
                        index=list(language_map.keys()).index(language)
                    )

                    selected_pii = False
                    if selected_module_id == 4:
                        selected_pii = st.radio(
                            "Enable detecting Personal Identifiable Information (PII)?",
                            options=[True, False],
                            index=1,
                            format_func=lambda x: "Yes" if x else "No",
                            horizontal=True
                        )

                    selected_uploaded = "File"
                    uploaded_files = None
                    uploaded_record = None

                    if selected_module_id == 4:
                        selected_uploaded = st.radio(
                            "What strategy do you want to upload?",
                            options=["File", "Record"],
                            horizontal=True
                        )
                        if selected_uploaded == "File":
                            uploaded_files = st.file_uploader(
                                "Choose a File",
                                type=selected_src_types,
                                help="Limit 200MB",
                                accept_multiple_files=True
                            )
                        elif selected_uploaded == "Record":
                            uploaded_record = st.audio_input("Record a voice message")

                    elif selected_module_id != 6:
                        uploaded_files = st.file_uploader(
                            "Choose a File",
                            type=selected_src_types,
                            help="Limit 200MB",
                            accept_multiple_files=False
                        )

                    
                    uploaded_transcription = []
                    if selected_module_id == 6:
                        
                        transcription_container = st.empty()
                        status_caption = st.empty()

                        # Path del JSON
                        output_dir = Path(f"files/{username}/module-ai-speech-to-realtime")
                        output_dir.mkdir(parents=True, exist_ok=True)
                        json_path = output_dir / "transcription.json"

                        # Cargar contenido existente
                        if json_path.exists() and json_path.stat().st_size > 0:
                            with open(json_path, "r", encoding="utf-8") as f:
                                uploaded_transcription = json.load(f)
                        else:
                            uploaded_transcription = []

                        # Mostrar transcripciones cargadas inicialmente
                        def render_transcriptions(partial_text=None):
                            transcription_html = ""

                            for item in uploaded_transcription:
                                transcription_html += f"""
                                    <div style="background-color:#21232B; padding:10px; border-radius:5px; margin-bottom:10px;">
                                        <div style="display:flex; justify-content:space-between;">
                                            <div style="width:35px; background-color:#E6A538; color:black; border-radius:5px; margin:2px; display:flex; align-items:center; justify-content:center;">
                                                {item['id']}</div>
                                            <div style="width:100%; margin:2px; padding:5px;">{item['transcription']}</div>
                                        </div>
                                    </div>
                                """
                            
                            # Agregar transcripción parcial si existe
                            if partial_text:
                                transcription_html += f"""
                                    <div style="background-color:#2A2A2A; padding:10px; border-radius:5px; margin-bottom:10px; opacity:0.6;">
                                        <div style="display:flex; justify-content:space-between;">
                                            <div style="width:35px; background-color:#AAAAAA; color:black; border-radius:5px; margin:2px; display:flex; align-items:center; justify-content:center;">
                                                •••</div>
                                            <div style="width:100%; margin:2px; padding:5px;">{partial_text}</div>
                                        </div>
                                    </div>
                                """

                            with transcription_container.container(border=True):
                                st.markdown(":speech_balloon: :red[Real-Time] ***Customer Voice Transcription***")
                                components.html(f"""
                                    <div id="scrollable-transcription" style="height:550px; overflow-y:auto; background-color:#1e1e1e; padding:10px; border-radius:10px; color:white; font-family:monospace;">
                                        {transcription_html}
                                    </div>
                                    <script>
                                        var div = window.parent.document.querySelectorAll('iframe[srcdoc]')[window.parent.document.querySelectorAll('iframe[srcdoc]').length - 1].contentWindow.document.getElementById('scrollable-transcription');
                                        if (div) div.scrollTop = div.scrollHeight;
                                    </script>
                                """, height=570)

                        render_transcriptions()

                        # Transcripción final → guardar y actualizar vista
                        def display_transcription_final(transcription):
                            print(f"Received final results: {transcription}")
                            transcription_id = len(uploaded_transcription) + 1
                            timestamp = datetime.now().isoformat()

                            new_record = {
                                "id": transcription_id,
                                "transcription": transcription,
                                "timestamp": timestamp
                            }

                            uploaded_transcription.append(new_record)

                            with open(json_path, "w", encoding="utf-8") as f:
                                json.dump(uploaded_transcription, f, ensure_ascii=False)

                            render_transcriptions()  # Redibuja sin parcial

                        # Transcripción parcial → solo renderiza
                        def display_transcription_partial(transcription):
                            print(f"Received partial results: {transcription}")
                            render_transcriptions(partial_text=transcription)

                        # Estado inicial de los botones
                        if "transcription_state" not in st.session_state:
                            st.session_state.transcription_state = "idle"  # "idle", "starting", "running", "stopped"

                        # Botones de control
                        btn_col1, btn_col2, btn_col3, btn_col4 = st.columns([2, 2, 2, 4])

                        # Botón Start
                        start_disabled = st.session_state.transcription_state == "stopped" or st.session_state.transcription_state == "idle"
                        if btn_col1.button("Start", type="primary", use_container_width=True, icon=":material/mic:", disabled=(not start_disabled)):
                            st.session_state.transcription_state = "running"
                            st.rerun()

                        # Botón Stop
                        stop_disabled = st.session_state.transcription_state != "running"
                        if btn_col2.button("Stop", type="secondary", use_container_width=True, icon=":material/stop_circle:", disabled=stop_disabled):
                            st.session_state.transcription_state = "stopped"
                            service.stop_realtime_session()
                            status_caption.markdown(":material/stop_circle: **:red[Transcription Stopped...]**")
                            st.rerun()

                        # Botón Reset
                        reset_disabled = bool(uploaded_transcription) and st.session_state.transcription_state != "running"
                        if btn_col3.button("Reset", type="secondary", use_container_width=True, icon=":material/cached:", disabled=(not reset_disabled)):
                            st.session_state.transcription_state = "idle"
                            service.stop_realtime_session()
                            uploaded_transcription.clear()
                            with open(json_path, "w", encoding="utf-8") as f:
                                json.dump([], f)
                            render_transcriptions()
                            status_caption.markdown(":material/cached: **:gray[Transcription Reset...]**")
                            st.rerun()

                        # Lógica de ejecución cuando se inicia transcripción
                        if st.session_state.transcription_state == "running":
                            status_caption.markdown(":material/mic: **:green[Starting Transcription...]**")

                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            language = language_map[selected_language_file]
                            loop.run_until_complete(
                                service.start_realtime_session(display_transcription_final, display_transcription_partial, language)
                            )



                    file_description = st.text_area("File Description")                    

                    # ← CAMBIO: Preparar lista de items a procesar: uno(s) archivo(s) o la grabación
                    files_to_process = []
                    
                    if selected_module_id == 4:
                        if selected_uploaded == "File":
                            files_to_process = uploaded_files if isinstance(uploaded_files, list) else [uploaded_files]
                        elif selected_uploaded == "Record":
                            files_to_process = [uploaded_record] if uploaded_record else []

                    elif selected_module_id == 6:
                        # Leer archivo JSON como entrada
                        if json_path.exists() and json_path.stat().st_size > 0:
                            with open(json_path, "r", encoding="utf-8") as f:
                                files_to_process = [json.load(f)]

                    else:
                        files_to_process = uploaded_files if uploaded_files else []
                        if not isinstance(files_to_process, list):
                            files_to_process = [files_to_process]
                    
                    # Radio: Target Type
                    if selected_trg_type:
                        if len(selected_trg_type) == 1:
                            trg_type = selected_trg_type[0]
                        else:
                            trg_type = st.radio(
                                "What would you1 like your target to be?",
                                options=selected_trg_type,
                                horizontal=True
                            )
                    else:
                        trg_type = None
                    
                    # ← CAMBIO: iteramos sobre cada archivo/grabación
                    for uploaded_file in files_to_process:

                        # Get file extension
                        if selected_module_id == 6:
                            file_extension = "json"
                        elif selected_uploaded == "Record":
                            file_extension = "wav"
                        elif selected_uploaded == "File" and uploaded_file:
                            file_extension = uploaded_file.name.rsplit(".", 1)[-1].lower()
                        else:
                            file_extension = ""
                        
                        # Module: [5] Multi-Modal RAG
                        if selected_module_id == 5:
                            if file_extension == "pdf":
                                # Validar número de páginas
                                pdf_document = fitz.open(stream=uploaded_file.read(), filetype="pdf")
                                if len(pdf_document) > 2:
                                    component.get_error("Only PDF documents with 2 pages or less are allowed.")
                                    pdf_document.close()
                                    uploaded_file = None
                                else:
                                    pdf_document.close()
                
                            file_src_strategy = st.radio(
                                "What strategy do you prefer to implement?",
                                options=["Single", "Double"] if file_extension == "pdf" else ["Single"]
                            )                    
                        
                        # Module: [2] Select IA
                        if (file_extension == "csv") and (selected_module_id == 1):
                            with st.expander("Data Dictionary (Optional)"):
                            
                                # Get column names for csv
                                df_comment = utl_function_service.get_csv_column_comments(uploaded_file)
                                
                                # Data Editor: Comment
                                comment_data_editor = st.data_editor(
                                    df_comment,
                                    use_container_width = True,
                                    hide_index          = True,
                                    num_rows            = "fixed",
                                    column_config       = {
                                        "Column Name" : st.column_config.TextColumn(disabled=True),
                                        "Comment"     : st.column_config.TextColumn()
                                    }
                                )
                

                    warning_msg = None

                    # Validar entrada según módulo y estrategia
                    if selected_module_id == 6:
                        if not uploaded_transcription or len(uploaded_transcription) == 0:
                            warning_msg = "Please load a valid real-time transcription."

                    elif selected_uploaded == "File":
                        if not uploaded_files:
                            warning_msg = "Please upload at least one valid file."

                    elif selected_uploaded == "Record":
                        if not uploaded_record:
                            warning_msg = "Please record a message."

                    # Validar descripción solo si ya hay entrada válida
                    if not warning_msg and (not file_description or not file_description.strip()):
                        warning_msg = "Please enter a valid description."

                    # Mensaje final si hubo error
                    if warning_msg:
                        st.warning(warning_msg, icon=":material/add_alert:")


                    btn_col1, btn_col2, btn_col3 = st.columns([2, 2.2, 6])

                    if btn_col1.button("Save", type="primary", use_container_width=True):
                        
                        if warning_msg:
                            st.stop()
                        
                        try:
                            component.get_processing(True)
                            utl_function_service.track_time(1)

                            # ← CAMBIO: iteramos sobre cada archivo/grabación
                            for uploaded_file in files_to_process:

                                # Variables
                                module_id           = selected_module_id
                                module_folder       = selected_module_folder
                                now_str             = datetime.now().strftime('%H%M%S%f')
                                file_name           = (uploaded_file.name if uploaded_file and hasattr(uploaded_file, "name") else f"rec_{now_str}.{file_extension or 'tmp'}")
                                prefix              = f"{username}/{module_folder}"
                                bucket_file_name    = (f"{prefix}/{file_name}").lower()
                                bucket_file_content = (json.dumps(uploaded_file, ensure_ascii=False, indent=2).encode("utf-8")
                                                       if selected_module_id == 6 else uploaded_file.getvalue() if uploaded_file else uploaded_record)
                                
                                # Upload file to Bucket
                                upload_file = bucket_service.upload_file(
                                    object_name     = bucket_file_name,
                                    put_object_body = bucket_file_content,
                                    msg             = True
                                )                            

                                if upload_file:
                                    # Set Variables
                                    file_src_file_name = utl_function_service.get_valid_url_path(file_name=bucket_file_name)
                                    file_src_size      = (json_path.stat().st_size if selected_module_id == 6 and json_path.exists()
                                                          else uploaded_file.size if uploaded_file and hasattr(uploaded_file, "size")
                                                          else uploaded_record.size if uploaded_record else 0)
                                    file_trg_obj_name  = (utl_function_service.get_valid_table_name(schema=f"SEL_AI_USER_ID_{user_id}", file_name=file_name)
                                                          if trg_type == "Autonomous Database"
                                                          else f"{file_src_file_name.rsplit('.', 1)[0]}_trg.{trg_type.lower()}")
                                    file_trg_language = language_map[selected_language_file]
                                    file_trg_pii      = 0
                                    file_description  = file_description
                                    # Insert File
                                    msg, file_id = db_file_service.insert_file(
                                        file_name,
                                        user_id,
                                        module_id,
                                        file_src_file_name,
                                        file_src_size,
                                        file_src_strategy,
                                        file_trg_obj_name,
                                        file_trg_language,
                                        file_trg_pii,
                                        file_description
                                    )
                                    component.get_toast(msg, icon=":material/database:")
                                    
                                    # Modules
                                    match module_id:
                                        case 1:
                                            msg = db_file_service.update_extraction(file_id, str(bucket_file_content))
                                            component.get_toast(msg, ":material/database:")
                        
                                            msg_module = select_ai_service.create(
                                                user_id,
                                                file_src_file_name, 
                                                file_trg_obj_name,
                                                comment_data_editor
                                            )
                                            file_trg_obj_name       = file_trg_obj_name
                                            file_trg_tot_pages      = 1
                                            file_trg_tot_characters = len(bucket_file_content)
                                            file_trg_tot_time       = utl_function_service.track_time(0)
                                            file_trg_language       = language_map[selected_language_file]
                                        case 2:
                                            msg = db_file_service.update_extraction(file_id, str(bucket_file_content))
                                            component.get_toast(msg, ":material/database:")
                                            
                                            msg_module = select_ai_rag_service.create_profile(
                                                user_id,
                                                file_src_file_name
                                            )
                                            file_trg_obj_name       = select_ai_rag_service.get_index_name(user_id)
                                            file_trg_tot_pages      = 1
                                            file_trg_tot_characters = len(bucket_file_content)
                                            file_trg_tot_time       = utl_function_service.track_time(0)
                                            file_trg_language       = language_map[selected_language_file]
                                        case 3:
                                            object_name = bucket_file_name
                                            msg_module, data = document_undestanding_service.create(
                                                object_name,
                                                prefix,
                                                language,
                                                file_id
                                            )
                                            file_trg_obj_name       = file_trg_obj_name
                                            file_trg_tot_pages      = data[-1].get('page_number', 0) if data else 0
                                            file_trg_tot_characters = sum(page.get('characters', 0) for page in data) if data else 0
                                            file_trg_tot_time       = utl_function_service.track_time(0)
                                            file_trg_language       = language_map[selected_language_file]
                                        case 4:
                                            object_name = bucket_file_name
                                            msg_module, data = speech_service.create_job(
                                                object_name,
                                                prefix,
                                                language,
                                                file_id,
                                                trg_type
                                            )
                                            file_trg_obj_name       = file_trg_obj_name
                                            file_trg_tot_pages      = 1
                                            file_trg_tot_characters = len(str(data))
                                            file_trg_tot_time       = utl_function_service.track_time(0)
                                            file_trg_language       = language_map[selected_language_file]
                                        case 5:
                                            object_name = bucket_file_name
                                            strategy    = file_src_strategy
                                            agent_id    = selected_agent_id
                                            msg_module, data = document_multimodal.create(
                                                object_name,
                                                strategy,
                                                user_id,
                                                agent_id,
                                                file_id,
                                                username
                                            )
                                            file_trg_obj_name       = file_trg_obj_name
                                            file_trg_tot_pages      = 1
                                            file_trg_tot_characters = len(str(data))
                                            file_trg_tot_time       = utl_function_service.track_time(0)
                                            file_trg_language       = language_map[selected_language_file]
                                        case 6:
                                            object_name = bucket_file_name
                                            msg_module, data = speech_service.create(
                                                object_name,
                                                prefix,
                                                language,
                                                file_id,
                                                trg_type
                                            )
                                            file_trg_obj_name       = file_trg_obj_name
                                            file_trg_tot_pages      = 1
                                            file_trg_tot_characters = len(str(data))
                                            file_trg_tot_time       = utl_function_service.track_time(0)
                                            file_trg_language       = language_map[selected_language_file]
                                            
                                            # Real-Time Transcription
                                            service.stop_realtime_session()
                                            uploaded_transcription.clear()
                                            with open(json_path, "w", encoding="utf-8") as f:
                                                json.dump([], f)
                                            render_transcriptions()
                                            status_caption.caption("")

                                    # Update Extraction
                                    file_trg_tot_time = utl_function_service.track_time(0)
                                    db_file_service.update_file(
                                        file_id,
                                        file_trg_obj_name,
                                        file_trg_tot_pages,
                                        file_trg_tot_characters,
                                        file_trg_tot_time,
                                        file_trg_language
                                    )

                                    # PII
                                    if selected_pii:
                                        # Set Variables
                                        file_trg_obj_name   = f"{file_src_file_name.rsplit('.', 1)[0]}_trg_pii.{trg_type.lower()}"
                                        file_trg_pii        = (1 if selected_pii else 0)

                                        # Insert File
                                        msg, file_id = db_file_service.insert_file(
                                            file_name,
                                            user_id,
                                            module_id,
                                            file_src_file_name,
                                            file_src_size,
                                            file_src_strategy,
                                            file_trg_obj_name,
                                            file_trg_language,
                                            file_trg_pii,
                                            file_description
                                        )
                                        component.get_toast(msg, icon=":material/database:")

                                        object_name = bucket_file_name
                                        msg_module, data = anomaly_engine_service.create(
                                            object_name,
                                            language,
                                            file_id,
                                            data,
                                            trg_type
                                        )
                                        file_trg_obj_name       = file_trg_obj_name
                                        file_trg_tot_pages      = 1
                                        file_trg_tot_characters = len(str(data))
                                        file_trg_tot_time       = utl_function_service.track_time(0)
                                        file_trg_language       = language_map[selected_language_file]

                                        # Update Extraction
                                        file_trg_tot_time = utl_function_service.track_time(0)
                                        db_file_service.update_file(
                                            file_id,
                                            file_trg_obj_name,
                                            file_trg_tot_pages,
                                            file_trg_tot_characters,
                                            file_trg_tot_time,
                                            file_trg_language
                                        )

                                    db_module_service.get_modules_files_cache(user_id, force_update=True)
                                    db_file_service.get_all_files_cache(user_id, force_update=True)

                                    component.get_success(msg_module)
                                    st.session_state["show_form_app"] = False
                                    st.rerun()

                        except Exception as e:
                            component.get_error(f"[Error] Uploading File:\n{e}")
                        finally:
                            component.get_processing(False)

                    if btn_col2.button("Cancel", use_container_width=True):
                        st.session_state["show_form_app"] = False
                        st.rerun()
                else:
                    st.warning("No modules found for this user.", icon=":material/warning:")

            elif mode == "view":
                col1, col2 = st.columns(2)
                with col1:
                    st.text_input("ID", value=data["FILE_ID"], disabled=True)
                    st.text_input("Size", value=str(data["FILE_SRC_SIZE"]), disabled=True)
                    st.text_input("NLS", value=data["FILE_TRG_LANGUAGE"], disabled=True)
                    st.text_input("Pages", value=str(data["FILE_TRG_TOT_PAGES"]), disabled=True)
                    st.text_input("Time", value=str(data["FILE_TRG_TOT_TIME"]), disabled=True)
                    st.text_input("Owner", value=str(data["USER_USERNAME"]), disabled=True)
                    st.text_input("Ver.", value=data["FILE_VERSION"], disabled=True)

                with col2:
                    st.text_input("Module", value=data["MODULE_NAME"], disabled=True)
                    st.text_input("Strategy", value=data["FILE_SRC_STRATEGY"], disabled=True)
                    st.text_input("PII", value=data["FILE_TRG_PII"], disabled=True)
                    st.text_input("Chars.", value=str(data["FILE_TRG_TOT_CHARACTERS"]), disabled=True)
                    st.text_input("Change", value=data["FILE_DATE"], disabled=True)
                    st.text_input("Owner Email", value=str(data["USER_EMAIL"]), disabled=True)
                    st.text_input("Status", value=data["Status"], disabled=True)
                    
                st.text_input("Input", value=data["FILE_SRC_FILE_NAME"], disabled=True)
                st.text_input("Output", value=data["FILE_TRG_OBJ_NAME"], disabled=True)
                st.text_input("Description", value=data["FILE_DESCRIPTION"], disabled=True)
                st.text_area("Text", value=data["FILE_TRG_EXTRACTION"], disabled=True, height=500)
                
                btn_col1, btn_col2 = st.columns([2.2, 8])

                if btn_col1.button("Cancel", use_container_width=True):
                    st.session_state["show_form_app"] = False
                    st.rerun()

            elif mode == "share":
                file_id = data["FILE_ID"]

                # Usuarios ya compartidos para este archivo
                df = db_file_service.get_all_file_user_cache(user_id, force_update=True)
                
                # Obtener el grupo del usuario actual
                is_admin = data["USER_GROUP_ID"] == 0  

                # Cargar usuarios disponibles
                if is_admin:
                    df_users = db_user_service.get_all_users_cache(force_update=True)
                    st.caption("You are sharing as **Administrator**. All users are available.")
                    row_users = df[df["FILE_ID"] == file_id]["USER_ID"].tolist()
                else:
                    df_users = db_user_service.get_all_user_group_shared_cache(user_id, force_update=True)
                    row_users = df[(df["FILE_ID"] == file_id) & (df["USER_GROUP_ID"] == user_group_id)]["USER_ID"].tolist()
                
                # Si no hay usuarios disponibles, mostrar mensaje
                if df_users.empty:
                    st.warning("There are no users available to share this file with.", icon=":material/person_off:")
                else:
                    old_users = row_users

                    selected_user_ids = st.pills(
                        "Select Users to Share With",
                        options=df_users["USER_ID"],
                        format_func=lambda uid: f"{uid}: {df_users.loc[df_users['USER_ID'] == uid, 'USER_USERNAME'].values[0]}",
                        selection_mode="multi",
                        default=old_users,
                        disabled=df_users.empty
                    )

                    new_users = selected_user_ids

                btn_col1, btn_col2, _ = st.columns([2, 2.2, 5.8])

                if btn_col1.button("Save", type="primary", use_container_width=True, disabled=df_users.empty):
                    try:
                        if set(old_users) != set(new_users):
                            component.get_processing(True)
                            msg = db_file_service.update_file_user(file_id, new_users)
                            component.get_success(msg, icon=":material/update:")
                            db_file_service.get_all_file_user_cache(user_id, force_update=True)
                            db_file_service.get_all_files_cache(user_id, force_update=True)
                            st.session_state["show_form_app"] = False
                            st.rerun()
                        else:
                            st.warning("No changes detected.")
                    except Exception as e:
                        component.get_error(f"[Error] Updating shared users:\n{e}")
                    finally:
                        component.get_processing(False)

                if btn_col2.button("Cancel", use_container_width=True):
                    st.session_state["show_form_app"] = False
                    st.rerun()

    # Toggle form state
    if not st.session_state["show_form_app"]:
        btn_col1, btn_col2 = st.columns([2, 8])

        if btn_col1.button("Create", type="primary", use_container_width=True):
            st.session_state["show_form_app"] = True
            st.session_state["form_mode_app"] = "create"
            st.session_state["selected_file"] = None
            st.rerun()
 
# conda activate oracle-ai
# streamlit run app.py --server.port 8501

# cd app && conda activate oracle-ai && streamlit run app.py --server.port 8501
