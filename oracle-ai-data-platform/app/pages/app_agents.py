import streamlit as st
import pandas as pd

import components as component
import services.database as database
import utils as utils

# Initialize services
db_module_service = database.ModuleService()
db_agent_service = database.AgentService()
db_user_service = database.UserService()

login = component.get_login()
component.get_footer()

map_agent_state = {1: "Active", 2: "Inactive", 0: "Delete"}
reverse_map_agent_state = {v: k for k, v in map_agent_state.items()}

if "show_form_agents" not in st.session_state:
    st.session_state["show_form_agents"] = False
    st.session_state["form_mode_agents"] = "create"
    st.session_state["selected_agent"] = None

if login:
    st.header(":material/smart_toy: Agents")
    st.caption("Manage agents for model.")

    user_id = st.session_state["user_id"]
    user_group_id = st.session_state["user_group_id"]
    df_agents = db_agent_service.get_all_agents_cache(user_id, force_update=True)
    df_models = db_agent_service.get_all_models()
    df_users = db_user_service.get_all_users_cache()

    if not st.session_state["show_form_agents"]:
        with st.container(border=True):
            st.badge("List Agents")

            if df_agents.empty:
                st.info("No agents found.")
            else:
                df_view = df_agents.copy()
                df_view["Edit"] = False
                df_view["Share"] = False
                df_view["Delete"] = False

                df_display = df_view[["AGENT_ID", "AGENT_NAME", "AGENT_DESCRIPTION", "AGENT_USERS", "AGENT_DATE", "USER_ID_OWNER", "USER_ID", "OWNER", "USER_EMAIL", "USER_USERNAME", "Edit", "Share","Delete"]]
                
                edited_df = st.data_editor(
                    df_display,
                    key="data-agent-list",
                    column_config={                        
                        "USER_EMAIL": None,
                        "OWNER": None,
                        "USER_ID_OWNER": None,
                        "USER_ID": None,
                        "AGENT_ID": st.column_config.Column("ID", disabled=True),
                        "AGENT_NAME": st.column_config.Column("Name", disabled=True),
                        "AGENT_DESCRIPTION": st.column_config.Column("Description", disabled=True),
                        "USER_USERNAME": st.column_config.Column("Owner", disabled=True),
                        "AGENT_USERS": st.column_config.Column("Share", disabled=True),
                        "AGENT_DATE": st.column_config.Column("Change", disabled=True),
                        "Edit": st.column_config.CheckboxColumn("Edit"),
                        "Share": st.column_config.CheckboxColumn("Share"),
                        "Delete": st.column_config.CheckboxColumn("Delete")
                    },
                    use_container_width=True,
                    hide_index=True
                )

                btn_col1, btn_col2, btn_col3, btn_col4 = st.columns([2, 2.2, 2.2, 3.8])

                if btn_col1.button("Edit", type="secondary", use_container_width=True, icon=":material/edit:"):
                    rows = edited_df[edited_df["Edit"]]
                    if rows.empty:
                        st.warning("Please select at least one agent to edit.")
                    else:
                        agent_id = rows.iloc[0]["AGENT_ID"]
                        data = df_view[df_view["AGENT_ID"] == agent_id].iloc[0].to_dict()
                        st.session_state.update({
                            "show_form_agents": True,
                            "form_mode_agents": "edit",
                            "selected_agent": data
                        })
                        st.rerun()

                if btn_col2.button("Share", type="secondary", use_container_width=True, icon=":material/share:"):
                    rows = edited_df[edited_df["Share"] == True]
                    
                    if rows.empty:
                        st.warning("Please select at least one agent to share.", icon=":material/add_alert:")
                    else:
                        for _, selected_row in rows.iterrows():
                            # Validar si el usuario es el propietario del archivo
                            if selected_row["USER_ID"] != selected_row["USER_ID_OWNER"]:
                                owner_email = selected_row.get("USER_EMAIL", "unknown@email.com")
                                st.warning(f"Only the agent owner can manage sharing. Please contact: **{owner_email}**", icon=":material/error:")
                                continue

                            # Abrir formulario de compartición
                            agent_id = rows.iloc[0]["AGENT_ID"]
                            data = df_view[df_view["AGENT_ID"] == agent_id].iloc[0].to_dict()
                            st.session_state.update({
                                "show_form_agents": True,
                                "form_mode_agents": "share",
                                "selected_agent": data
                            })
                            st.rerun()

                if btn_col3.button("Delete", type="secondary", use_container_width=True, icon=":material/delete:"):
                    try:
                        rows_to_edit = edited_df[edited_df["Delete"] == True]
                        if rows_to_edit.empty:
                            st.warning("Please select at least one agent to delete.", icon=":material/add_alert:")
                        else:
                            component.get_processing(True)

                            for _, row in rows_to_edit.iterrows():
                                agent_id = row["AGENT_ID"]
                                agent_name = row["AGENT_NAME"].rsplit("/", 1)[-1]
                                shared_users = row.get("AGENT_USERS", 0)

                                if row["OWNER"] == 1:
                                    if shared_users > 0:
                                        st.warning(
                                            f"Agent '{agent_name}' cannot be deleted because it has been shared with {shared_users} user(s).",
                                            icon=":material/block:"
                                        )
                                else:
                                    # Solo remover acceso
                                    msg = db_agent_service.delete_agent_user_by_user(agent_id, user_id, agent_name)
                                    component.get_success(msg, icon=":material/remove_circle:")

                            db_agent_service.get_all_agents_cache(user_id, force_update=True)

                    except Exception as e:
                        component.get_error(f"[Error] Deleting File:\n{e}")
                    finally:
                        component.get_processing(False)

    if st.session_state["show_form_agents"]:
        mode = st.session_state["form_mode_agents"]

        with st.container(border=True):
            st.badge(
                "Create Agent" if mode == "create" else "Edit Agent" if mode == "edit" else "Share Agent",
                color="green" if mode == "create" else "blue" if mode == "edit" else "orange"
            )
            data = st.session_state["selected_agent"]

            if mode == "create" or mode == "edit":
                agent_data = {
                    "AGENT_NAME": "",
                    "AGENT_DESCRIPTION": "",
                    "AGENT_TYPE": "Chat",
                    "AGENT_MODEL_ID": None,
                    "AGENT_MAX_OUT_TOKENS": 1000,
                    "AGENT_TEMPERATURE": 0.5,
                    "AGENT_TOP_P": 0.9,
                    "AGENT_TOP_K": 50,
                    "AGENT_FREQUENCY_PENALTY": 0,
                    "AGENT_PRESENCE_PENALTY": 0,
                    "AGENT_PROMPT_SYSTEM": "",
                    "AGENT_PROMPT_MESSAGE": ""
                } if mode == "create" else st.session_state["selected_agent"]

                name = st.text_input("Name", value=agent_data["AGENT_NAME"], disabled=(mode == "edit"))
                desc = st.text_input("Description", value=agent_data["AGENT_DESCRIPTION"])

                agent_type = st.selectbox("Agent Type", ["Chat", "Extraction"], index=0 if agent_data["AGENT_TYPE"] == "Chat" else 1)
                filtered_models = df_models if agent_type == "Chat" else df_models[df_models["AGENT_MODEL_TYPE"] == "vlm"]

                model_ids = filtered_models["AGENT_MODEL_ID"].tolist()
                model_index = model_ids.index(agent_data["AGENT_MODEL_ID"]) if agent_data["AGENT_MODEL_ID"] in model_ids else 0

                selected_model_id = st.selectbox(
                    "Which model would you like to use?",
                    options=model_ids,
                    index=model_index,
                    format_func=lambda mid: f"{mid}: {filtered_models.loc[filtered_models['AGENT_MODEL_ID'] == mid, 'AGENT_MODEL_NAME'].values[0]}"
                )

                col1, col2 = st.columns([0.4, 0.6])
                with col1:
                    st.caption("Parameters")
                    max_tokens = st.number_input("Max Tokens", 1, 4000, int(agent_data["AGENT_MAX_OUT_TOKENS"]))
                    temp = st.number_input("Temperature", 0.0, 1.0, float(agent_data["AGENT_TEMPERATURE"]), step=0.1)
                    top_p = st.number_input("Top P", 0.0, 1.0, float(agent_data["AGENT_TOP_P"]), step=0.05)
                    top_k = st.number_input("Top K", 0, 500, int(agent_data["AGENT_TOP_K"]), step=1)
                    freq_penalty = st.number_input("Frequency Penalty", -2.0, 2.0, float(agent_data["AGENT_FREQUENCY_PENALTY"]), step=0.1)
                    pres_penalty = st.number_input("Presence Penalty", -2.0, 2.0, float(agent_data["AGENT_PRESENCE_PENALTY"]), step=0.1)

                with col2:
                    if agent_type == "Chat":
                        prompt_sys = st.text_area("Agent Prompt System", value=agent_data["AGENT_PROMPT_SYSTEM"], height=110, max_chars=4000)
                        prompt_msg = st.text_area("Agent Prompt Message", value=agent_data["AGENT_PROMPT_MESSAGE"], height=341, max_chars=4000, help="{context}")
                    else:
                        prompt_sys = st.text_area("Agent Prompt System", value=agent_data["AGENT_PROMPT_SYSTEM"], height=496, max_chars=4000)
                        prompt_msg = ""

                btn_col1, btn_col2, btn_col3 = st.columns([2, 2.2, 6])

                if btn_col1.button("Save", type="primary", use_container_width=True):
                    if agent_type == "Chat" and "{context}" not in prompt_msg:
                        component.get_error("For 'Chat' agents, 'Agent Prompt Message' must contain '{context}'.")
                    else:
                        try:
                            component.get_processing(True)
                            if mode == "create":
                                msg, _ = db_agent_service.insert_agent(
                                    agent_model_id=selected_model_id,
                                    agent_name=name,
                                    agent_description=desc,
                                    agent_type=agent_type,
                                    agent_max_out_tokens=max_tokens,
                                    agent_temperature=temp,
                                    agent_top_p=top_p,
                                    agent_top_k=top_k,
                                    agent_frequency_penalty=freq_penalty,
                                    agent_presence_penalty=pres_penalty,
                                    agent_prompt_system=prompt_sys,
                                    agent_prompt_message=prompt_msg,
                                    user_id=user_id
                                )
                                component.get_success(msg, ":material/add_row_below:")
                            else:
                                msg = db_agent_service.update_agent(
                                    agent_data["AGENT_ID"],
                                    name,
                                    desc,
                                    max_tokens,
                                    temp,
                                    top_p,
                                    top_k,
                                    freq_penalty,
                                    pres_penalty,
                                    reverse_map_agent_state.get(agent_data.get("Status", "Active"), 1)
                                )
                                component.get_success(msg, ":material/update:")

                            db_agent_service.get_all_agents_cache(user_id, force_update=True)
                            st.session_state["show_form_agents"] = False
                            st.rerun()

                        except Exception as e:
                            component.get_error(f"[Error] {'Creating' if mode == 'create' else 'Updating'} Agent:\n{e}")
                        finally:
                            component.get_processing(False)

                if btn_col2.button("Cancel", use_container_width=True):
                    st.session_state["show_form_agents"] = False
                    st.rerun()

            elif mode == "share":
                agent_id = data["AGENT_ID"]
                
                # Usuarios ya compartidos para este agente
                df = db_agent_service.get_all_agent_user_cache(user_id, force_update=True)
                
                # Obtener el grupo del usuario actual
                is_admin = data["USER_GROUP_ID"] == 0  

                # Cargar usuarios disponibles
                if is_admin:
                    df_users = db_user_service.get_all_users_cache(force_update=True)
                    st.caption("You are sharing as **Administrator**. All users are available.")
                    row_users = df[(df["AGENT_ID"] == agent_id)]["USER_ID"].tolist()
                else:
                    df_users = db_user_service.get_all_user_group_shared_cache(user_id, force_update=True)
                    row_users = df[(df["AGENT_ID"] == agent_id) & (df["USER_GROUP_ID"] == user_group_id)]["USER_ID"].tolist()
                
                # Si no hay usuarios disponibles, mostrar mensaje
                if df_users.empty:
                    st.warning("There are no users available to share this agent with.", icon=":material/person_off:")
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
                            msg = db_agent_service.update_agent_user(agent_id, new_users)
                            component.get_success(msg, icon=":material/update:")
                            db_agent_service.get_all_agent_user_cache(user_id, force_update=True)
                            db_agent_service.get_all_agents_cache(user_id, force_update=True)
                            st.session_state["show_form_agents"] = False
                            st.rerun()
                        else:
                            st.warning("No changes detected.")
                    except Exception as e:
                        component.get_error(f"[Error] Updating shared Agents:\n{e}")
                    finally:
                        component.get_processing(False)

                if btn_col2.button("Cancel", use_container_width=True):
                    st.session_state["show_form_agents"] = False
                    st.rerun()


    # Toggle form state
    if not st.session_state["show_form_agents"]:
        btn_col1, btn_col2 = st.columns([2, 8])
        
        if btn_col1.button("Create", type="primary", use_container_width=True):
            st.session_state["show_form_agents"] = True
            st.session_state["form_mode_agents"] = "create"
            st.session_state["selected_agent"] = None
            st.rerun()