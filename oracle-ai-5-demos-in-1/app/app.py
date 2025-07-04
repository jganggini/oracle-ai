from datetime import datetime
import streamlit as st
import fitz
import re

import components as component
import services.database as database
import services as service
import utils as utils

# Crear una instancia del servicio
db_module_service             = database.ModuleService()
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

# Streamlit app configuration
st.set_page_config(
    page_title="Demos | Oracle AI",
    page_icon="🅾️"
)

component.get_login()
component.get_footer()

if "username" in st.session_state and "user_id" in st.session_state:
    st.header(":material/upload_file: Upload File")
    st.caption("Manage files.")
    
    # Get Sessions
    username    = st.session_state["username"]
    user_id     = st.session_state["user_id"]
    language    = st.session_state["language"]

    # Variables: Default
    file_src_strategy   = None
    trg_type            = None
    comment_data_editor = None

    # Get Modules
    df_modules = db_module_service.get_modules_cache(user_id).drop_duplicates("MODULE_ID")
    df_agents  = db_module_service.get_modules_cache(user_id, force_update=True)[lambda df: (df["MODULE_VECTOR_STORE"] == 1) & (df["AGENT_TYPE"].isin(['Extraction']))]

    if not df_modules.empty:
        with st.container(border=True):
            
            # Selectbox: Modules
            selected_module_id = st.selectbox(
                "Which module would you like to start with?",
                options=df_modules["MODULE_ID"],
                format_func=lambda module_id: f"{module_id}: {df_modules.loc[df_modules['MODULE_ID'] == module_id, 'MODULE_NAME'].squeeze()}"
            )
            
            if selected_module_id:
                # Get module row data
                module_data = df_modules.loc[df_modules["MODULE_ID"] == selected_module_id].iloc[0]
                
                # Ensure AGENT_ID exists in df_modules before accessing it
                if not df_modules[df_modules["AGENT_ID"] == selected_module_id].empty:
                    agent_id = df_modules.loc[df_modules["AGENT_ID"] == selected_module_id].iloc[0]
                else:
                    agent_id = None

                # Get selected [module_id]
                module_name = module_data["MODULE_NAME"]

                # Get selected [module_folder]
                selected_module_folder = module_data["MODULE_FOLDER"]

                # Get selected [module_src_types]
                selected_src_types = utl_function_service.get_list_to_str(module_data["MODULE_SRC_TYPE"])

                # Get selected [module_trg_type] 
                selected_trg_type  = utl_function_service.get_list_to_str(module_data["MODULE_TRG_TYPE"])
                
                df_agents = df_agents[df_agents["MODULE_ID"] == selected_module_id].copy()

                if not df_agents.empty:
                    df_agents["AGENT_ID"] = df_agents["AGENT_ID"].astype(int)
                    selected_agent_id = st.selectbox(
                        "with which agent?",
                        options=df_agents["AGENT_ID"],
                        format_func=lambda agent_id: f"{agent_id}: {df_agents.loc[df_agents['AGENT_ID'] == agent_id, 'AGENT_NAME'].values[0]} ({df_agents.loc[df_agents['AGENT_ID'] == agent_id, 'AGENT_TYPE'].values[0]})"
                    )
                
                # Selectbox: Modules
                selected_language_file = st.selectbox(
                    "What is the language of the file?",
                    options = list(language_map.keys()),
                    index   = list(language_map.keys()).index(language)
                )

                selected_pii = None
                if selected_module_id in [4]:
                    # Radio: OCI Language
                    selected_pii = st.radio(
                        "Enable detecting Personal Identifiable Information (PII)?",
                        options=[True, False],
                        index=1,
                        format_func=lambda x: "Yes" if x else "No",
                        horizontal=True
                    )
                else:
                    selected_pii = False
                    
                selected_uploaded = None
                if selected_module_id==4:
                    # Radio: Uploaded
                    selected_uploaded = st.radio(
                        "What strategy do you uploaded?",
                        options=["File", "Record"],
                        horizontal=True
                    )
                else:
                    selected_uploaded="File"
                
                uploaded_file = None
                uploaded_record = None
                if selected_uploaded=="File":
                    # Uploader: File
                    uploaded_file = st.file_uploader(
                        "Choose a File",
                        type = selected_src_types,
                        help = "Limit 200MB",
                        accept_multiple_files = False
                    )
                else:
                    uploaded_record = st.audio_input("Record a voice message")

                if (selected_uploaded=="File" and uploaded_file) or (selected_uploaded=="Record" and uploaded_record):
                    # Get file extension
                    file_extension = uploaded_file.name.rsplit(".", 1)[-1].lower() if (selected_uploaded=="File" and uploaded_file) else "wav"
                    
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

                    

                    # Radio: Target Type
                    trg_type = st.radio(
                        "What would you like your target to be?",
                        options=selected_trg_type
                    ) if selected_trg_type else None

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

                    # Architecture
                    with st.expander("Architecture"):
                        architecture_image = f"-{file_src_strategy}" if file_src_strategy else ""
                        st.image(f"images/{module_name}{architecture_image}.gif")
                
                # Botón de submit, deshabilitado si no hay archivo                
                upload_button = st.button(
                    "Upload",
                    disabled=not (
                        (selected_uploaded == "Record" and uploaded_record) or
                        (selected_uploaded == "File" and uploaded_file)
                    )
                )
        
                if upload_button and (uploaded_file or uploaded_record):                  
                    try:
                        component.get_processing(True)
                        utl_function_service.track_time(1)
                        
                        # Variables
                        module_id           = selected_module_id
                        module_folder       = selected_module_folder
                        file_name           = uploaded_file.name if uploaded_file else f"rec_{datetime.now().strftime('%H%M%S%f')}.wav"
                        prefix              = f"{username}/{module_folder}"
                        bucket_file_name    = (f"{prefix}/{file_name}").lower()
                        bucket_file_content = uploaded_file.getvalue() if uploaded_file else uploaded_record
                        
                        # Upload file to Bucket
                        upload_file = bucket_service.upload_file(
                            object_name     = bucket_file_name,
                            put_object_body = bucket_file_content,
                            msg             = True
                        )                            

                        if upload_file:
                            # Set Variables
                            file_src_file_name = utl_function_service.get_valid_url_path(file_name=bucket_file_name)
                            file_src_size      = (uploaded_file.size if uploaded_file else uploaded_record.size)
                            file_trg_obj_name  = (
                                utl_function_service.get_valid_table_name(schema=f"SEL_AI_USER_ID_{user_id}", file_name=file_name)
                                if trg_type == "Autonomous Database"
                                else f"{file_src_file_name.rsplit('.', 1)[0]}_trg.{trg_type.lower()}"
                            )
                            file_trg_language       = language_map[selected_language_file]
                            file_trg_pii            = 0

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
                                file_trg_pii
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
                                    msg_module, data = speech_service.create(
                                        object_name,
                                        prefix,
                                        language,
                                        file_id
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
                                file_trg_obj_name   = f"{file_src_file_name.rsplit('.', 1)[0]}_trg_pii.srt"
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
                                    file_trg_pii
                                )
                                component.get_toast(msg, icon=":material/database:")

                                object_name = bucket_file_name
                                msg_module, data = anomaly_engine_service.create(
                                    object_name,
                                    language,
                                    file_id,
                                    data
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

                    except Exception as e:
                        component.get_error(f"[Error] Uploading File:\n{e}")
                    finally:
                        component.get_processing(False)

            else:
                st.warning("No modules found for this user.", icon=":material/warning:")

    # Get list of files 
    st.subheader("File List")
    df_files = db_file_service.get_all_files_cache(user_id)

    if not df_files.empty:
        # Copy data for editing
        df_display = df_files.copy()
        
        # Add a 'Status' column and Map numeric states to text
        df_display["Status"] = df_display["FILE_STATE"].map(map_state)
        
        # Add a 'Delete' column for the checkbox
        df_display["Delete"] = False

        # Data Editor: File
        file_data_editor = st.data_editor(
            df_display,
            use_container_width = True,
            hide_index          = True,
            num_rows            = "fixed",
            column_config       = {
                "USER_ID"        : None,
                "MODULE_ID"      : None,
                "FILE_STATE"     : None,
                "FILE_ID": st.column_config.Column(
                    "ID",
                    disabled=True
                ),
                "MODULE_NAME": st.column_config.Column(
                    "Module",
                    disabled=True
                ),
                "FILE_SRC_FILE_NAME": st.column_config.LinkColumn(
                    "Input",
                    display_text=r".*/(.+)$",
                    help="Click to open the document",
                    disabled=True
                ),
                "FILE_SRC_SIZE": st.column_config.Column(
                    "Size",
                    disabled=True
                ),
                "FILE_SRC_STRATEGY": st.column_config.Column(
                    "Strategy",
                    disabled=True
                ),
                "FILE_TRG_OBJ_NAME": st.column_config.LinkColumn(
                    "Output",
                    display_text=r".*/(.+)$",
                    help="Click to open the document",
                    disabled=True
                ),
                "FILE_TRG_LANGUAGE": st.column_config.Column(
                    "NLS",
                    disabled=True
                ),
                "FILE_TRG_PII": st.column_config.Column(
                    "PII",
                    disabled=True
                ),
                "FILE_TRG_TOT_PAGES": st.column_config.Column(
                    "Pages",
                    disabled=True
                ),
                "FILE_TRG_TOT_CHARACTERS": st.column_config.Column(
                    "Chars.",
                    disabled=True
                ),
                "FILE_TRG_TOT_TIME": st.column_config.Column(
                    "Time",
                    disabled=True
                ),
                "FILE_DATE": st.column_config.Column(
                    "Change",
                    disabled=True
                ),
                "FILE_VERSION": st.column_config.Column(
                    "Ver.",
                    disabled=True
                ),
                "Status": st.column_config.Column(
                    "Status",
                    disabled=True
                ),
                "Delete": st.column_config.CheckboxColumn(
                    "Delete",
                    help="Check to delete this file",
                    default=False
                )
            }
        )
        
        # Get Changes to Dataframe
        df_changed_rows = utl_function_service.get_changes_to_df(
            original_df     = df_display,
            edited_df       = file_data_editor,
            compare_cols    = ["Delete"]
        )

        # Enable or disable the "Apply Changes" button
        if not df_changed_rows.empty:
            if st.button("Delete", type="primary"):
                try:
                    component.get_processing(True)
                                        
                    for _, row in df_changed_rows.iterrows():
                        utl_function_service.track_time(1)

                        # Variables
                        file_id            = row["FILE_ID"]
                        module_id          = row["MODULE_ID"]
                        file_src_file_name = row["FILE_SRC_FILE_NAME"]
                        file_name          = file_src_file_name.rsplit("/", 1)[-1]
                        object_name        = file_src_file_name.split('/o/')[-1]
                        file_state         = reverse_map_state.get(row["Status"], 1)
                        
                        if row["Delete"] == True:
                            # Delete file to Bucket
                            delete_object = bucket_service.delete_object(object_name)
                            
                            # Eliminar el archivo si Delete es True
                            if delete_object:                                
                                msg = db_file_service.delete_file(file_name, file_id)
                                component.get_success(msg, icon=":material/database:")

                            # Modules
                            match module_id:
                                case 1:
                                    select_ai_service.create_profile(user_id)
                                case 2:
                                    select_ai_rag_service.create_profile(user_id, file_src_file_name)
                                case 3:
                                    obj_name_pdf  = f"{object_name.rsplit('.', 1)[0]}_trg.pdf"
                                    obj_name_json = f"{object_name.rsplit('.', 1)[0]}_trg.json"
                                    
                                    # Delete file to Bucket
                                    delete_object_pdf  = bucket_service.delete_object(obj_name_pdf)
                                    delete_object_json = bucket_service.delete_object(obj_name_json)
                                case _:
                                    print("Coming Soon...")

                            db_module_service.get_modules_files_cache(user_id, force_update=True)
                            db_file_service.get_all_files_cache(user_id, force_update=True)
                
                except Exception as e:
                    component.get_error(f"[Error] Deleting File:\n{e}")
                finally:
                    component.get_processing(False)
        else:
            # If no changes, disable the button
            st.button("Delete", type="primary", disabled=True)
        
    else:
        st.info("No files found.", icon=":material/info:")

# conda activate oracle-ai
# streamlit run app.py --server.port 8501

# cd app && conda activate oracle-ai && streamlit run app.py --server.port 8501
