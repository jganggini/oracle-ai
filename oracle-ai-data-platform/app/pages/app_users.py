import streamlit as st
import pandas as pd
import json

import components as component
import services.database as database
import utils as utils

# Initialize service instances
db_user_service     = database.UserService()
db_select_ai_service = database.SelectAIService()
db_module_service    = database.ModuleService()
db_agent_service     = database.AgentService()
utl_function_service = utils.FunctionService()

# Load login and footer components
login = component.get_login()
component.get_footer()

# User state mapping
map_user_state = {1: "Active", 2: "Inactive", 0: "Delete"}
reverse_map_user_state = {v: k for k, v in map_user_state.items()}

# Check if session is authenticated
if login:
    st.header(":material/settings_account_box: Users")

    # Load data from database
    df_modules    = db_module_service.get_all_modules()
    df_users      = db_user_service.get_all_users_cache()
    df_user_group = db_user_service.get_all_user_group_cache()

    # Init session state for form control
    if "show_form_users" not in st.session_state:
        st.session_state["show_form_users"] = False
        st.session_state["form_mode_users"] = "create"
        st.session_state["selected_user"] = None

    # Render user list only if form is not visible
    if not st.session_state["show_form_users"]:

        # Module legend
        module_legend = "\n".join([f"{row['MODULE_ID']}: {row['MODULE_NAME']}" for _, row in df_modules.iterrows()])
        st.caption("Legend (Modules):")
        st.code(module_legend, language="markdown")

        # User table view
        with st.container(border=True):
            st.badge("List User")

            if df_users.empty:
                st.info("No users found.")
            else:
                df_view = df_users.copy()
                df_view["Modules"] = df_view["USER_MODULES"].apply(lambda x: ", ".join(str(mid) for mid in eval(x)) if isinstance(x, str) else ", ".join(str(mid) for mid in x))
                df_view["State"] = df_view["USER_STATE"].map(map_user_state)
                df_view["Edit"] = False
                df_view["Delete"] = False
                df_display = df_view[["USER_ID", "USER_USERNAME", "USER_GROUP_NAME", "Modules", "State", "Edit", "Delete"]]

                edited_df = st.data_editor(
                    df_display,
                    column_config={
                        "Edit": st.column_config.CheckboxColumn("Edit", help="Mark row to edit"),
                        "USER_ID": "ID",
                        "USER_USERNAME": "Username",
                        "USER_GROUP_NAME": "Group",
                    },
                    disabled=["USER_ID", "USER_USERNAME", "USER_GROUP_NAME", "Modules", "State"],
                    hide_index=True,
                )

                btn_col1, btn_col2, btn_col3 = st.columns([2, 2, 6])

                if btn_col1.button("Edit", type="secondary", use_container_width=True, icon=":material/edit:"):
                    rows_to_edit = edited_df[edited_df["Edit"] == True]
                    if rows_to_edit.empty:
                        st.warning("Please select at least one user to edit.", icon=":material/add_alert:")
                    else:
                        for _, selected_row in rows_to_edit.iterrows():
                            user_id = selected_row["USER_ID"]
                            data = df_users[df_users["USER_ID"] == user_id].iloc[0].to_dict()
                            st.session_state.update({
                                "show_form_users": True,
                                "form_mode_users": "edit",
                                "selected_user": data
                            })
                            st.rerun()

                if btn_col2.button("Delete", type="secondary", use_container_width=True, icon=":material/delete:"):
                    try:
                        rows_to_edit = edited_df[edited_df["Delete"] == True]
                        if rows_to_edit.empty:
                            st.warning("Please select at least one user to delete.", icon=":material/add_alert:")
                        else:
                            component.get_processing(True)

                            for _, row in rows_to_edit.iterrows():
                                user_id = row["USER_ID"]
                                username = row["USER_USERNAME"]

                                msg = db_user_service.delete_user(user_id, username)
                                component.get_success(msg, icon=":material/remove_circle:")

                            db_user_service.get_all_users_cache(force_update=True)

                    except Exception as e:
                        component.get_error(f"[Error] Deleting File:\n{e}")
                    finally:
                        component.get_processing(False)

    # User form (create/edit)
    if st.session_state["show_form_users"]:
        mode = st.session_state["form_mode_users"]

        with st.container(border=True):
            st.badge(
                "Create User" if mode == "create" else "Edit User" if mode == "edit" else "Bulk Users",
                color="green" if mode == "create" else "blue" if mode == "edit" else "orange")
            
            if mode == "create" or mode == "edit":
                data = {
                    "USER_GROUP_ID": None,
                    "USER_USERNAME": "",
                    "USER_PASSWORD": "",
                    "USER_NAME": "",
                    "USER_LAST_NAME": "",
                    "USER_EMAIL": "correo@dominio.com",
                    "USER_MODULES": []
                } if mode == "create" else st.session_state["selected_user"]

                if isinstance(data["USER_MODULES"], str):
                    data["USER_MODULES"] = eval(data["USER_MODULES"])

                col1, col2 = st.columns(2)
                with col1:
                    username = st.text_input("Username", value=data["USER_USERNAME"], disabled=(mode == "edit"))
                    password = st.text_input("Password", type="password") if mode == "create" else "---"
                with col2:
                    name = st.text_input("First Name", value=data["USER_NAME"])
                    last_name = st.text_input("Last Name", value=data["USER_LAST_NAME"])

                group_options = df_user_group["USER_GROUP_ID"].tolist()
                default_group_idx = group_options.index(data["USER_GROUP_ID"]) if data["USER_GROUP_ID"] in group_options else 0

                selected_group_id = st.selectbox(
                    "User Group:",
                    options=group_options,
                    index=default_group_idx,
                    format_func=lambda x: f"{x}: {df_user_group.loc[df_user_group['USER_GROUP_ID'] == x, 'USER_GROUP_NAME'].values[0]}"
                )

                email = st.text_input("Email", value=data["USER_EMAIL"])

                modules_selected = st.pills(
                    "Modules",
                    options=df_modules["MODULE_ID"],
                    format_func=lambda mid: f"{mid}: {df_modules.loc[df_modules['MODULE_ID'] == mid, 'MODULE_NAME'].values[0]}",
                    selection_mode="multi",
                    default=data["USER_MODULES"],
                    key="modules_selection"
                )

            elif mode == "bulk":

                uploaded_file = st.file_uploader("Upload CSV File", type=["csv"])

                if uploaded_file is not None:
                    df_upload = pd.read_csv(uploaded_file)
                    required_columns = ["USER_GROUP_NAME", "USERNAME", "PASSWORD", "FIRST_NAME", "LAST_NAME", "EMAIL", "MODULE_IDS"]

                    if not all(col in df_upload.columns for col in required_columns):
                        st.error(f"CSV must contain columns: {', '.join(required_columns)}")
                    else:
                        st.dataframe(df_upload)

                        # Detectar grupos inexistentes por nombre
                        existing_group_names = df_user_group["USER_GROUP_NAME"].tolist()
                        missing_group_names = sorted(set(df_upload["USER_GROUP_NAME"]) - set(existing_group_names))

                        new_group_info = {}
                        group_warnings = []

                        for group_name in missing_group_names:
                            with st.expander(f"Create Group: {group_name}"):
                                name_input = st.text_input("Group Name", value=group_name, key=f"name_{group_name}", disabled=True)
                                desc_input = st.text_area("Description", key=f"desc_{group_name}")
                                new_group_info[group_name] = {"name": name_input, "description": desc_input}

                                if not name_input or not desc_input:
                                    group_warnings.append(f"Missing name or description for group '{group_name}'")

                        for warn in group_warnings:
                            st.warning(warn, icon=":material/add_alert:")

                        btn_col1, btn_col2 = st.columns([2, 8])

            btn_col1, btn_col2, btn_col3 = st.columns([2, 2.2, 6])

            if btn_col1.button("Save", type="primary", use_container_width=True):
                try:
                    component.get_processing(True)
                    sel_ai_password = utl_function_service.get_password()

                    if mode == "create":
                        if not all([username, password if mode == "create" else True, name, last_name, email, modules_selected]):
                            component.get_error("Please fill in all fields.")
                        else:
                            msg, user_id = db_user_service.insert_user(
                                user_group_id   = selected_group_id,
                                username        = username,
                                password        = password,
                                sel_ai_password = sel_ai_password,
                                name            = name,
                                last_name       = last_name,
                                email           = email,
                                modules         = json.dumps(modules_selected)
                            )
                            component.get_success(msg, ":material/add_row_below:")

                            if 1 in modules_selected:
                                db_select_ai_service.drop_user(user_id)
                                msg = db_select_ai_service.create_user(user_id, sel_ai_password)
                                component.get_toast(msg, ":material/database:")

                            relevant_modules = [m for m in modules_selected if m not in [0, 1, 2]]
                            if relevant_modules:
                                msg = db_agent_service.copy_agent_to_admin(user_id)
                                component.get_toast(msg, ":material/database:")

                    elif mode == "edit":
                        state = reverse_map_user_state.get(data.get("Status", "Active"), 1)
                        msg = db_user_service.update_user(
                            data["USER_ID"], selected_group_id, username, name, last_name, email, state,
                            modules=json.dumps(modules_selected)
                        )
                        component.get_success(msg, ":material/update:")

                        user_id = data["USER_ID"]

                        if 1 in modules_selected:
                            db_select_ai_service.drop_user(user_id)
                            msg = db_select_ai_service.create_user(user_id, sel_ai_password)
                            component.get_toast(msg, ":material/database:")

                        relevant_modules = [m for m in modules_selected if m not in [0, 1, 2]]
                        if relevant_modules:
                            msg = db_agent_service.copy_agent_to_admin(user_id)
                            component.get_toast(msg, ":material/database:")
                    
                    elif mode == "bulk":
                        try:
                            if group_warnings:
                                st.stop()

                            component.get_processing(True)

                            # Crear nuevos grupos y mapear sus IDs reales
                            group_name_to_id = {}

                            for group_name, info in new_group_info.items():
                                msg, group_id = db_user_service.insert_user_group(
                                    user_group_name=info["name"],
                                    user_group_description=info["description"]
                                )
                                group_name_to_id[group_name] = group_id
                                st.success(f"{msg} (ID {group_id})")

                            # Refrescar caché de grupos
                            df_user_group = db_user_service.get_all_user_group_cache(force_update=True)

                            # Agregar grupos existentes al mapeo
                            for _, row in df_user_group.iterrows():
                                group_name_to_id[row["USER_GROUP_NAME"]] = row["USER_GROUP_ID"]

                            # Insertar usuarios
                            for _, row in df_upload.iterrows():
                                group_name        = row["USER_GROUP_NAME"]
                                selected_group_id = int(group_name_to_id.get(group_name))
                                username          = str(row["USERNAME"])
                                password          = str(row["PASSWORD"])
                                first_name        = str(row["FIRST_NAME"])
                                last_name         = str(row["LAST_NAME"])
                                email             = str(row["EMAIL"])
                                modules_selected  = json.loads(row["MODULE_IDS"]) if isinstance(row["MODULE_IDS"], str) else row["MODULE_IDS"]
                                modules_str       = json.dumps([int(m) for m in modules_selected])
                                sel_ai_password   = utl_function_service.get_password()

                                msg, user_id = db_user_service.insert_user(
                                    user_group_id   = selected_group_id,
                                    username        = username,
                                    password        = password,
                                    sel_ai_password = sel_ai_password,
                                    name            = first_name,
                                    last_name       = last_name,
                                    email           = email,
                                    modules         = modules_str
                                )

                                component.get_success(msg, ":material/add_row_below:")

                                # Procesamiento adicional por módulos
                                if 1 in modules_selected:
                                    db_select_ai_service.drop_user(user_id)
                                    msg = db_select_ai_service.create_user(user_id, sel_ai_password)
                                    component.get_toast(msg, ":material/database:")

                                relevant_modules = [m for m in modules_selected if m not in [0, 1, 2]]
                                if relevant_modules:
                                    msg = db_agent_service.copy_agent_to_admin(user_id)
                                    component.get_toast(msg, ":material/database:")

                            db_user_service.get_all_users_cache(force_update=True)
                            st.session_state["show_form_users"] = False
                            st.rerun()

                        except Exception as e:
                            component.get_error(f"[Error] Bulk Upload:\n{e}")

                        finally:
                            component.get_processing(False)

                    db_user_service.get_all_users_cache(force_update=True)
                    st.session_state["show_form_users"] = False
                    st.rerun()

                except Exception as e:
                    component.get_error(f"[Error] {'Creating' if mode == 'create' else 'Updating'} User:\n{e}")
                finally:
                    component.get_processing(False)

            if btn_col2.button("Cancel", use_container_width=True):
                st.session_state["show_form_users"] = False
                st.rerun()

        
       

    # Toggle form state
    if not st.session_state["show_form_users"]:
        btn_col1, btn_col2, btn_col3 = st.columns([2, 2.2, 6])

        if btn_col1.button("Create", type="primary", use_container_width=True):
            st.session_state["show_form_users"] = True
            st.session_state["form_mode_users"] = "create"
            st.session_state["selected_user"] = None
            st.rerun()
        
        if btn_col2.button("Bulk", type="secondary", use_container_width=True):
            st.session_state["show_form_users"] = True
            st.session_state["form_mode_users"] = "bulk"
            st.session_state["selected_user"] = None
            st.rerun()