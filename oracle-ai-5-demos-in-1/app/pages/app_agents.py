import streamlit as st

import components as component
import services.database as database
import utils as utils

# Crear una instancia del servicio
db_module_service = database.ModuleService()

component.get_login()
component.get_footer()

if "username" in st.session_state and "user_id" in st.session_state:
    st.header(":material/tune: Agents Tuning")
    st.caption("Manage agents for model.")

    # Get Sessions
    user_id = st.session_state["user_id"]

    # Conexión a la BD y carga de datos
    df_agents = db_module_service.get_modules_cache(user_id, force_update=True)[lambda df: (df["MODULE_VECTOR_STORE"] == 1) & (df["AGENT_TYPE"].isin(['Chat', 'Extraction']))]
    
    df_models = db_module_service.get_all_models()

    # Get Modules
    if not df_agents.empty:
        with st.container(border=True):
            # Selectbox: Modules
            df_agents["AGENT_ID"] = df_agents["AGENT_ID"].astype(int)
            selected_agent_id = st.selectbox(
                "Which agent would you like to start with?",
                options=df_agents["AGENT_ID"],
                format_func=lambda agent_id: f"{agent_id}: {df_agents.loc[df_agents['AGENT_ID'] == agent_id, 'AGENT_NAME'].values[0]} ({df_agents.loc[df_agents['AGENT_ID'] == agent_id, 'AGENT_TYPE'].values[0]})",
                index=None,
                placeholder="Select Agent..."
            )

            if selected_agent_id:
                # Get module row data
                agent_data = df_agents.loc[df_agents["AGENT_ID"] == selected_agent_id].iloc[0]

                # Store original user data for change detection
                original_data = {
                    "model_id"                : agent_data["MODEL_ID"] ,
                    "agent_max_out_tokens"    : agent_data["AGENT_MAX_OUT_TOKENS"],
                    "agent_temperature"       : agent_data["AGENT_TEMPERATURE"],
                    "agent_top_p"             : agent_data["AGENT_TOP_P"],
                    "agent_top_k"             : agent_data["AGENT_TOP_K"],
                    "agent_frequency_penalty" : agent_data["AGENT_FREQUENCY_PENALTY"],
                    "agent_presence_penalty"  : agent_data["AGENT_PRESENCE_PENALTY"],
                    "agent_prompt_system"     : agent_data["AGENT_PROMPT_SYSTEM"],
                    "agent_prompt_message"    : agent_data["AGENT_PROMPT_MESSAGE"]
                }

                # Obtener el modelo asociado al módulo seleccionado
                agent_id = agent_data["AGENT_ID"]
                
                # Obtener el modelo asociado al módulo seleccionado
                module_id = agent_data["MODULE_ID"]                

                if ("module_id_old" not in st.session_state):
                    st.session_state["module_id_old"] = module_id
                    
                    st.session_state["max_out_tokens_slider"] = agent_data["AGENT_MAX_OUT_TOKENS"]
                    st.session_state["max_out_tokens_number"] = agent_data["AGENT_MAX_OUT_TOKENS"]

                    st.session_state["temperature_slider"] = agent_data["AGENT_TEMPERATURE"]
                    st.session_state["temperature_number"] = agent_data["AGENT_TEMPERATURE"]

                    st.session_state["top_p_slider"] = agent_data["AGENT_TOP_P"]
                    st.session_state["top_p_number"] = agent_data["AGENT_TOP_P"]

                    st.session_state["top_k_slider"] = agent_data["AGENT_TOP_K"]
                    st.session_state["top_k_number"] = agent_data["AGENT_TOP_K"]

                    st.session_state["frequency_penalty_slider"] = agent_data["AGENT_FREQUENCY_PENALTY"]
                    st.session_state["frequency_penalty_number"] = agent_data["AGENT_FREQUENCY_PENALTY"]
                
                elif (st.session_state["module_id_old"] != module_id):
                    st.session_state["module_id_old"] = module_id
                    
                    st.session_state["max_out_tokens_slider"] = agent_data["AGENT_MAX_OUT_TOKENS"]
                    st.session_state["max_out_tokens_number"] = agent_data["AGENT_MAX_OUT_TOKENS"]

                    st.session_state["temperature_slider"] = agent_data["AGENT_TEMPERATURE"]
                    st.session_state["temperature_number"] = agent_data["AGENT_TEMPERATURE"]

                    st.session_state["top_p_slider"] = agent_data["AGENT_TOP_P"]
                    st.session_state["top_p_number"] = agent_data["AGENT_TOP_P"]

                    st.session_state["top_k_slider"] = agent_data["AGENT_TOP_K"]
                    st.session_state["top_k_number"] = agent_data["AGENT_TOP_K"]

                    st.session_state["frequency_penalty_slider"] = agent_data["AGENT_FREQUENCY_PENALTY"]
                    st.session_state["frequency_penalty_number"] = agent_data["AGENT_FREQUENCY_PENALTY"]
                
                elif("max_out_tokens_slider" not in st.session_state):
                    st.session_state["module_id_old"] = module_id
                    
                    st.session_state["max_out_tokens_slider"] = agent_data["AGENT_MAX_OUT_TOKENS"]
                    st.session_state["max_out_tokens_number"] = agent_data["AGENT_MAX_OUT_TOKENS"]

                    st.session_state["temperature_slider"] = agent_data["AGENT_TEMPERATURE"]
                    st.session_state["temperature_number"] = agent_data["AGENT_TEMPERATURE"]

                    st.session_state["top_p_slider"] = agent_data["AGENT_TOP_P"]
                    st.session_state["top_p_number"] = agent_data["AGENT_TOP_P"]

                    st.session_state["top_k_slider"] = agent_data["AGENT_TOP_K"]
                    st.session_state["top_k_number"] = agent_data["AGENT_TOP_K"]

                    st.session_state["frequency_penalty_slider"] = agent_data["AGENT_FREQUENCY_PENALTY"]
                    st.session_state["frequency_penalty_number"] = agent_data["AGENT_FREQUENCY_PENALTY"]
                
                # Obtener el modelo asociado al módulo seleccionado
                model_id = agent_data["MODEL_ID"]

                # Filtrar opciones de modelo basadas en AGENT_TYPE
                if agent_data["AGENT_TYPE"] == "Chat":
                    # Si no es "Extraction", incluir todos los modelos
                    model_options = df_models["MODEL_ID"].tolist()
                elif agent_data["AGENT_TYPE"] == "Extraction":
                    # Filtrar modelos donde MODEL_TYPE sea 'vlm'
                    model_options = df_models.loc[df_models["MODEL_TYPE"] == "vlm", "MODEL_ID"].tolist()

                # Determinar el índice predeterminado
                model_index = model_options.index(model_id) if model_id in model_options else 0

                # Selectbox para modelos
                selected_model_id = st.selectbox(
                    "Which model would you like to see?",
                    options=model_options,
                    format_func=lambda model_id: f"{model_id}: {df_models.loc[df_models['MODEL_ID'] == model_id, 'MODEL_NAME'].values[0]}",
                    index=model_index
                )

                pcol1, pcol2 = st.columns([0.40, 0.60])

                with pcol1:
                    
                    if selected_model_id:
                        
                        agent_name = st.text_input(
                            label="Module Name",
                            value=agent_data["MODULE_NAME"] if isinstance(agent_data["MODULE_NAME"], str) else agent_data["MODULE_NAME"].iloc[0],
                            disabled=True,
                        )
                        
                        # Obtener el "MODEL_PROVIDER" basado en el modelo seleccionado
                        model_provider = df_models.loc[df_models["MODEL_ID"] == selected_model_id, "MODEL_PROVIDER"].values[0]
                        
                        st.caption("Parameters")
                        
                        col1, col2 = st.columns([0.7, 0.3])
                        with col1:
                            st.slider(
                                "Max. Tokens",
                                min_value=1,
                                max_value=(4000),
                                step=1,
                                key="max_out_tokens_slider",
                                help="The maximum number of tokens to generate for the output.",
                                on_change=lambda: st.session_state.update({"max_out_tokens_number": st.session_state["max_out_tokens_slider"]})
                            )
                        with col2:
                            agent_max_out_tokens = st.number_input(
                                label="None",
                                label_visibility="hidden",
                                min_value=1,
                                max_value=(4000),
                                step=1,
                                key="max_out_tokens_number",
                                on_change=lambda: st.session_state.update({"max_out_tokens_slider": st.session_state["max_out_tokens_number"]})
                            )

                        # Temperature
                        if "temperature" not in st.session_state:
                            st.session_state["temperature"] = 1.0

                        col1, col2 = st.columns([0.7, 0.3])
                        with col1:
                            st.slider(
                                "Temperature",
                                min_value=0.0,
                                max_value=1.0,
                                step=0.1,
                                key="temperature_slider",
                                help="Adjust the randomness of the generated output.",
                                on_change=lambda: st.session_state.update({"temperature_number": st.session_state["temperature_slider"]})
                            )
                        with col2:
                            agent_temperature = st.number_input(
                                label="None",
                                label_visibility="hidden",
                                min_value=0.0,
                                max_value=1.0,
                                step=0.1,
                                key="temperature_number",
                                on_change=lambda: st.session_state.update({"temperature_slider": st.session_state["temperature_number"]})
                            )

                        # Top p
                        if "top_p" not in st.session_state:
                            st.session_state["top_p"] = 1.0

                        col1, col2 = st.columns([0.7, 0.3])
                        with col1:
                            st.slider(
                                "Top p",
                                min_value=0.0,
                                max_value=1.0,
                                step=0.05,
                                key="top_p_slider",
                                help="Consider tokens with cumulative probability up to p.",
                                on_change=lambda: st.session_state.update({"top_p_number": st.session_state["top_p_slider"]})
                            )
                        with col2:
                            agent_top_p = st.number_input(
                                label="None",
                                label_visibility="hidden",
                                min_value=0.0,
                                max_value=1.0,
                                step=0.05,
                                key="top_p_number",
                                on_change=lambda: st.session_state.update({"top_p_slider": st.session_state["top_p_number"]})
                            )

                        # Top k
                        if "top_k" not in st.session_state:
                            st.session_state["top_k"] = 0

                        col1, col2 = st.columns([0.7, 0.3])
                        with col1:
                            st.slider(
                                "Top k",
                                min_value=0,
                                max_value=500,
                                step=1,
                                key="top_k_slider",
                                help="Generate outputs using the top k most likely tokens.",
                                on_change=lambda: st.session_state.update({"top_k_number": st.session_state["top_k_slider"]})
                            )
                        with col2:
                            agent_top_k = st.number_input(
                                label="None",
                                label_visibility="hidden",
                                min_value=0,
                                max_value=500,
                                step=1,
                                key="top_k_number",
                                on_change=lambda: st.session_state.update({"top_k_slider": st.session_state["top_k_number"]})
                            )

                        # Penalización por frecuencia
                        if "top_k" not in st.session_state:
                            st.session_state["top_k"] = 0

                        col1, col2 = st.columns([0.7, 0.3])
                        with col1:
                            st.slider(
                                "Frequency Penalty",
                                min_value=-2.0,
                                max_value=2.0,
                                step=0.1,
                                key="frequency_penalty_slider",
                                help="Penalizes tokens based on frequency in the output so far.",
                                on_change=lambda: st.session_state.update({"frequency_penalty_number": st.session_state["frequency_penalty_slider"]})
                            )
                        with col2:
                            agent_frequency_penalty = st.number_input(
                                label="None",
                                label_visibility="hidden",
                                min_value=-2.0,
                                max_value=2.0,
                                step=0.1,
                                key="frequency_penalty_number",
                                on_change=lambda: st.session_state.update({"frequency_penalty_slider": st.session_state["frequency_penalty_number"]})
                            )

                        # Penalización por frecuencia
                        col1, col2 = st.columns([0.7, 0.3])
                        with col1:
                            st.slider(
                                "Presence Penalty",
                                min_value=-2.0,
                                max_value=2.0,
                                step=0.1,
                                key="presence_penalty_slider",
                                help="Penalizes tokens that have already appeared in the output.",
                                on_change=lambda: st.session_state.update({"presence_penalty_number": st.session_state["presence_penalty_slider"]})
                            )
                        with col2:
                            agent_presence_penalty = st.number_input(
                                label="None",
                                label_visibility="hidden",
                                min_value=-2.0,
                                max_value=2.0,
                                step=0.1,
                                key="presence_penalty_number",
                                on_change=lambda: st.session_state.update({"presence_penalty_slider": st.session_state["presence_penalty_number"]})
                            )

                with pcol2:
                    if selected_agent_id:
                        
                        # Filtrar opciones de modelo basadas en AGENT_TYPE
                        agent_prompt_message = ""
                        if agent_data["AGENT_TYPE"] == "Chat":
                            # Si no es "Extraction", incluir todos los modelos
                            agent_prompt_system = st.text_area(
                                key="agent_promt_system",
                                label="Agent Prompt System",
                                height=304,
                                max_chars=4000,
                                value=agent_data["AGENT_PROMPT_SYSTEM"],
                            )

                            agent_prompt_message = st.text_area(
                                key="agent_promt_message",
                                label="Agent Prompt Message",
                                height=304,
                                max_chars=4000,
                                value=agent_data["AGENT_PROMPT_MESSAGE"],
                                help="{context}"
                            )
                        elif agent_data["AGENT_TYPE"] == "Extraction":
                            # Filtrar modelos donde MODEL_TYPE sea 'vlm'
                            agent_prompt_system = st.text_area(
                                key="agent_promt_system",
                                label="Agent Prompt System",
                                height=672,
                                max_chars=4000,
                                value=agent_data["AGENT_PROMPT_SYSTEM"],
                            )
                        

                if st.button("Update", type="primary"):
                    try:
                        # Detect changes in the form
                        has_changes = (
                            selected_model_id          != original_data["model_id"]
                            or agent_max_out_tokens    != original_data["agent_max_out_tokens"]
                            or agent_temperature       != original_data["agent_temperature"]
                            or agent_top_p             != original_data["agent_top_p"]
                            or agent_top_k             != original_data["agent_top_k"]
                            or agent_frequency_penalty != original_data["agent_frequency_penalty"]
                            or agent_presence_penalty  != original_data["agent_presence_penalty"]
                            or agent_prompt_system     != original_data["agent_prompt_system"]
                            or agent_prompt_message    != original_data["agent_prompt_message"]
                        )

                        if not has_changes:
                            st.warning("No changes detected.")
                        elif not agent_prompt_system.strip():
                            st.warning("Please fill in all required fields.")
                        elif agent_data["AGENT_TYPE"] != "Extraction" and not agent_prompt_message.strip():
                            st.warning("Please fill in all required fields.")
                        elif "{context}" not in agent_prompt_message and agent_data["AGENT_TYPE"] != "Extraction":
                            st.warning("Agent Prompt Message. '{context}' is missing.")
                        else:
                            component.get_processing(True)
                            
                            # Update
                            msg = db_module_service.update_agent(
                                agent_id,
                                user_id,
                                selected_model_id,
                                agent_name,
                                agent_max_out_tokens,
                                agent_temperature,
                                agent_top_p,
                                agent_top_k,
                                agent_frequency_penalty,
                                agent_presence_penalty,
                                agent_prompt_system,
                                agent_prompt_message
                            )
                            st.success(msg, icon=":material/update:")

                            db_module_service.get_modules_cache(user_id, force_update=True)
                            st.rerun()

                    except Exception as e:
                        component.get_error(f"[Error] Update Agent:\n{e}")
                    finally:
                        component.get_processing(False)