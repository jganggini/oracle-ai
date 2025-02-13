import streamlit as st

import components as component
import services.database as database
import services as service
import utils as utils

# Crear una instancia del servicio
db_user_service   = database.UserService()
db_module_service = database.ModuleService()
db_select_ai_service = database.SelectAIService()

component.get_login()
component.get_footer()

if "username" in st.session_state and "user_id" in st.session_state:
    st.header(":material/view_module: Modules")
    st.caption("Manage modules for user.")

    # Conexión a la BD y carga de datos
    df_users   = db_user_service.get_all_users_cache()
    df_modules = db_module_service.get_all_modules()
        
    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            selected_user_id = st.selectbox(
                "Which user would you like to change?",
                options=df_users["USER_ID"],
                format_func=lambda user_id: f"{user_id}: {df_users.loc[df_users['USER_ID'] == user_id, 'USER_USERNAME'].values[0]}",
                placeholder="Select a user..."
            )

        # Mostrar los módulos como opciones en formato pills
        selected_module_id = st.pills(
            "Modules",
            options=df_modules["MODULE_ID"],
            format_func=lambda module_id: f"{module_id}: {df_modules.loc[df_modules['MODULE_ID'] == module_id, 'MODULE_NAME'].values[0]}",
            selection_mode="multi",
            default=df_users.loc[df_users["USER_ID"] == selected_user_id, "USER_MODULES"].values[0]
        )

        old_modules = df_users.loc[df_users["USER_ID"] == selected_user_id, "USER_MODULES"].values[0]
        new_modules = selected_module_id

        if st.button("Save", type="primary"):
            try:
                component.get_processing(True)
                
                if (old_modules != new_modules):
                    if all([selected_user_id, selected_module_id]):
                        
                        msg = db_user_service.update_modules(
                            selected_user_id,
                            selected_module_id
                        )
                        component.get_success(msg, icon=":material/update:")
                        
                        # Convertir old_modules y new_modules a conjuntos
                        old_modules = set(old_modules)
                        new_modules = set(new_modules)

                        print(f"old_modules: {old_modules}")
                        print(f"new_modules: {new_modules}")

                        # Evaluar módulo 1: Crear o eliminar
                        if (1 in old_modules) and (1 not in new_modules):
                            print("Eliminar módulo 1")
                            msg = db_select_ai_service.drop_user(selected_user_id)
                            component.get_toast(msg, icon=":material/database:")

                        if (1 not in old_modules) and (1 in new_modules):
                            print("Crear módulo 1")
                            sel_ai_password = df_users.loc[df_users["USER_ID"] == selected_user_id, "USER_SEL_AI_PASSWORD"].values[0]
                            db_select_ai_service.drop_user(selected_user_id)
                            msg = db_select_ai_service.create_user(selected_user_id, sel_ai_password)
                            component.get_toast(msg, icon=":material/database:")

                        # Evaluar módulos relevantes (3, 4, 5): Crear o eliminar
                        for module_id in {3, 4, 5}:
                            # Módulo relevante: Eliminar
                            if (module_id in old_modules) and (module_id not in new_modules):
                                print(f"Eliminar módulo: {module_id}")
                                msg = db_module_service.delete_agent(selected_user_id, module_id)
                                component.get_toast(msg, icon=":material/database:")

                            # Módulo relevante: Crear
                            if (module_id not in old_modules) and (module_id in new_modules):
                                print(f"Crear módulo: {module_id}")
                                msg = db_module_service.create_agent(selected_user_id, module_id)
                                component.get_toast(msg, icon=":material/database:")
                                

                        db_user_service.get_all_users_cache(force_update=True)
                    else:
                        st.error("Please fill in all required fields.")
                else:
                    st.warning("No changes detected.")
            
            except Exception as e:
                component.get_error(f"[Error] Update Modules:\n{e}")
            finally:
                component.get_processing(False)