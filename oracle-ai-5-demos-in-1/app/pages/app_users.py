import streamlit as st
import time

import components as component
import services.database as database
import utils as utils

# Crear una instancia del servicio
db_user_service = database.UserService()
db_select_ai_service = database.SelectAIService()
db_module_service = database.ModuleService()
utl_function_service = utils.FunctionService()

component.get_login()
component.get_footer()

# Map of user states: numeric -> text
map_user_state = {
    1: "Active",
    2: "Inactive",
    0: "Delete"
}

# Reverse mapping: text -> numeric
reverse_map_user_state = {v: k for k, v in map_user_state.items()}

if "username" in st.session_state and "user_id" in st.session_state:
    st.header(":material/settings_account_box: Users")
    st.caption("Manage users in a single editable table.")

    # Get DB connection
    df_modules = db_module_service.get_all_modules()
    df_users   = db_user_service.get_all_users_cache()

    # Add new user form
    st.subheader("Add New User")
    with st.form("form-user"):
        col1, col2 = st.columns(2)
        with col1:
            new_username = st.text_input("Username")
            new_name     = st.text_input("First Name")
        with col2:
            new_password  = st.text_input("Password", type="password")
            new_last_name = st.text_input("Last Name")
        new_email         = st.text_input("Email", value="correo@dominio.com")

        # Mostrar los módulos como opciones en los pills
        new_modules = st.pills(
            "Modules",
            options=df_modules["MODULE_ID"],
            format_func=lambda module_id: f"{module_id}: {df_modules.loc[df_modules['MODULE_ID'] == module_id, 'MODULE_NAME'].values[0]}",
            selection_mode="multi",
        )

        if st.form_submit_button("Create", type="primary"):
            try:
                component.get_processing(True)

                sel_ai_password = utl_function_service.get_password()

                # Basic validation
                if all([new_username, new_password, new_name, new_last_name, new_email, new_modules]):

                    msg, user_id = db_user_service.insert_user(
                        username        = new_username, 
                        password        = new_password,
                        sel_ai_password = sel_ai_password,
                        name            = new_name, 
                        last_name       = new_last_name, 
                        email           = new_email,
                        modules         = new_modules
                    )
                    component.get_success(msg, ":material/add_row_below:")

                    print(f"new_modules: {new_modules}")

                    # Construir una lista de módulos relevantes y el string `module_id_all`
                    relevant_modules = [module_id for module_id in new_modules if module_id not in [0, 1, 2]]
                    module_id_all = ",".join(map(str, relevant_modules))

                    print(f"relevant_modules: {relevant_modules}")
                    print(f"module_id_all: {module_id_all}")

                    for module_id in new_modules:
                        # Módulo 1: Ejecutar acciones específicas
                        if module_id == 1:
                            db_select_ai_service.drop_user(user_id)

                            msg = db_select_ai_service.create_user(user_id, sel_ai_password)
                            component.get_toast(msg, ":material/database:")

                    # Ejecutar `create_agent`
                    if relevant_modules:
                        msg = db_module_service.create_agent(user_id, module_id_all)
                        component.get_toast(msg, ":material/database:")
                        
                    db_user_service.get_all_users_cache(force_update=True)
                    
                else:
                    component.get_error(f"Please fill in all required fields.")
            
            except Exception as e:
                component.get_error(f"[Error] Creating User:\n{e}")
            finally:
                component.get_processing(False)

    # Display user list in editable table
    st.subheader("User List")
    
    if df_users.empty:
        st.info("No users found.")
    else:
        # Copy data for editing
        df_display = df_users.copy()

        # Map numeric states to text
        df_display["Status"] = df_display["USER_STATE"].map(map_user_state)

        # Add a 'Delete' column for the checkbox
        df_display["Delete"] = False

        # Reorder columns for display
        df_display = df_display[
            [
                "USER_ID", 
                "USER_USERNAME", 
                "USER_NAME", 
                "USER_LAST_NAME", 
                "USER_EMAIL",
                "USER_MODULES",
                "USER_DATE",
                "Status",
                "Delete"
            ]
        ]

        # Data editor for inline edits
        user_data_editor = st.data_editor(
            df_display,
            key="data-users",
            use_container_width=True,
            hide_index=True,
            num_rows="fixed",
            column_config={
                "USER_ID": st.column_config.Column(
                    "User ID",
                    disabled=True
                ),
                "USER_USERNAME": st.column_config.Column(
                    "Username",
                    disabled=True
                ),
                "USER_NAME": st.column_config.Column(
                    "Name"
                ),
                "USER_LAST_NAME": st.column_config.Column(
                    "Last Name"
                ),
                "USER_EMAIL": st.column_config.Column(
                    "Email"
                ),
                "USER_DATE": st.column_config.Column(
                    "Change",
                    disabled=True
                ),
                "USER_MODULES": st.column_config.Column(
                    "Modules"
                ),
                "Status": st.column_config.SelectboxColumn(
                    "Status",
                    options=["Active", "Inactive"],
                    required=True,
                    help="Toggle user's status"
                ),
                "Delete": st.column_config.CheckboxColumn(
                    "Delete",
                    help="Check to delete this user",
                    default=False
                )
            },
        )

        # Get Changes to Dataframe
        df_changed_rows = utl_function_service.get_changes_to_df(
            original_df     = df_display,
            edited_df       = user_data_editor,
            compare_cols    = [
                "USER_USERNAME", 
                "USER_NAME", 
                "USER_LAST_NAME", 
                "USER_EMAIL", 
                "Status",
                "Delete"
            ]
        )

        # Enable or disable the "Apply Changes" button
        if st.button("Apply Changes"):
            try:            
                if not df_changed_rows.empty:
                    component.get_processing(True)
                    
                    # Delete users marked with Delete=True
                    df_changed = df_changed_rows[df_changed_rows["Delete"] == True]

                    # Delete
                    if not df_changed.empty:
                        for _, row in df_changed.iterrows():
                            user_id       = row["USER_ID"]
                            user_username = row["USER_USERNAME"]
                            # Verificar y convertir user_modules si es necesario
                            user_modules = eval(row["USER_MODULES"]) if isinstance(row["USER_MODULES"], str) else row["USER_MODULES"]
                            
                            msg = db_user_service.delete_user(user_id, user_username)
                            component.get_success(msg, ":material/delete:")
                            
                            # Module> 1: Select AI
                            if 1 in user_modules:
                                # Ejecutar si existe el modulo 2 dentro de USER_MODULES
                                msg = db_select_ai_service.drop_user(user_id)
                                component.get_toast(msg, ":material/delete:")
                            
                    # Update
                    else:
                        for _, row in df_changed.iterrows():
                            id        = row["USER_ID"]
                            username  = row["USER_USERNAME"]
                            name      = row["USER_NAME"]
                            last_name = row["USER_LAST_NAME"]
                            email     = row["USER_EMAIL"]
                            state     = reverse_map_user_state.get(row["Status"], 1)
                            
                            msg = db_user_service.update_user(
                                id,
                                username,
                                name,
                                last_name,
                                email,
                                state
                            )
                            component.get_success(msg, ":material/update:")
                
                    db_user_service.get_all_users_cache(force_update=True)

                else:
                    st.info("No changes detected.")

            except Exception as e:
                component.get_error(f"[Error] Deleting User:\n{e}")
            finally:
                component.get_processing(False)

        