import streamlit as st

import components as component
import services.database as database
import utils as utils

# Crear una instancia del servicio
db_module_service = database.ModuleService()
db_user_service   = database.UserService()
utl_function_service = utils.FunctionService()

map_user_state = {
    1: "Active",
    2: "Inactive",
    0: "Delete"
}

login = component.get_login()
component.get_footer()

if login:
    st.header(":material/upload_file: Profile")
    st.caption("Manage profile.")

    df_modules   = db_module_service.get_all_modules()
    user_id      = st.session_state['user_id']
    df_user      = db_user_service.get_user(user_id).iloc[0]
    user_modules = eval(df_user["USER_MODULES"]) if isinstance(df_user["USER_MODULES"], str) else df_user["USER_MODULES"]

    # Store original user data for change detection
    original_data = {
        "username"  : df_user["USER_USERNAME"],
        "password"  : df_user["USER_PASSWORD"],
        "name"      : df_user["USER_NAME"],
        "last_name" : df_user["USER_LAST_NAME"],
        "email"     : df_user["USER_EMAIL"],
        "modules"   : df_user["USER_MODULES"],
        "state"     : df_user["USER_STATE"],
    }

    # Form for user profile update
    with st.form("form-profile"):
        col1, col2 = st.columns(2)
        with col1:
            username  = st.text_input("Username", value=original_data['username'], disabled=True)
            password1 = st.text_input("Password", type="password", value=original_data['password'])
            name      = st.text_input("First Name", value=original_data['name'])
        with col2:
            email     = st.text_input("Email", value=original_data['email'])
            password2 = st.text_input("Confirm Password", type="password", value=original_data['password'])
            last_name = st.text_input("Last Name", value=original_data['last_name'])

        # Display module options as pills
        modules = st.pills(
            "Modules",
            options        = df_modules["MODULE_ID"],
            format_func    = lambda module_id: f"{df_modules.loc[df_modules['MODULE_ID'] == module_id, 'MODULE_NAME'].values[0]}",
            selection_mode = "multi",
            default        = original_data['modules'],
            disabled       = True
        )

        # Display status options as pills
        state = st.pills(
            "Status",
            options     = list(map_user_state.keys()),
            format_func = lambda state_id: map_user_state[state_id],
            default     = original_data["state"]
        )

        # Submit button
        if st.form_submit_button("Update", type="primary"):
            try:
                component.get_processing(True)
                
                # Detect changes in the form
                has_changes = (
                    password1    != original_data["password"]
                    or name      != original_data["name"]
                    or last_name != original_data["last_name"]
                    or email     != original_data["email"]
                    or state     != original_data["state"]
                )

                if not has_changes:
                    st.warning("No changes detected.")
                else:
                    if not all([password1.strip(), password2.strip(), name.strip(), last_name.strip(), email.strip()]):
                        st.error("Please fill in all required fields.")
                    else:
                        if password1 != password2:
                            st.error("Passwords do not match.")
                        else:
                            if not utl_function_service.is_valid_password(password1):
                                st.error("Password does not meet the security requirements.")
                            else:
                                
                                # Update user profile
                                msg = db_user_service.update_profile(
                                    user_id,
                                    username,
                                    password1,
                                    name,
                                    last_name,
                                    email,
                                    state
                                )
                                st.success(msg, icon=":material/update:")
                
            except Exception as e:
                component.get_error(f"[Error] Update User:\n{e}")
            finally:
                component.get_processing(False)