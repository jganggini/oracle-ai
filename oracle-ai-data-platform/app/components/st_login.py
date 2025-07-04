import ast
import pandas as pd
import streamlit as st
import time

import services.database as database

# Create an instance of the UserService
db_user_service = database.UserService()

def parse_modules(modules):
    """
    Parse modules from a JSON-like string or a comma-separated string.

    Args:
        modules (str): A string representing modules in JSON or comma-separated format.

    Returns:
        list: A list of module names.
    """
    try:
        # Handle Python-style string list
        return ast.literal_eval(modules)
    except (ValueError, SyntaxError):
        # Fallback to comma-separated format
        return [m.strip().strip('"') for m in modules.strip('[]').split(',')]

def get_menu(modules, user):
    """
    Build and display the sidebar menu based on the user's modules.

    Args:
        modules (str): The user's accessible modules.
        user (str): The user's name to display in the sidebar.
    """
    module_list = parse_modules(modules)  # Parse the module list correctly
    
    with st.sidebar:
        st.image("images/st_pages.gif")
        
        with st.expander("Capabilities"):
            st.text("Enter a new era of productivity with generative AI capabilities built for business. Innovate with your choice of open source or proprietary large language models (LLMs). Leverage AI embedded as you need it across the full stack—apps, infrastructure, and more.")    
        
        st.write(f"Hi, **:blue-background[{user}]**")

        # Always shown links
        st.page_link("app.py", label="Knowledge", icon=":material/book_ribbon:")
        st.page_link("pages/app_agents.py", label="Agents", icon=":material/smart_toy:")

        # AI Demos Section
        ai_demos = [
            ("Select AI", "pages/app_chat_01.py", ":material/smart_toy:"),
            ("Select AI RAG", "pages/app_chat_02.py", ":material/plagiarism:"),
            ("Vector Database", "pages/app_chat_03.py", ":material/network_intelligence:")
        ]
        available_demos = [demo for demo in ai_demos if demo[0] in module_list]

        if available_demos:
            st.subheader("Chats")
            for label, page, icon in available_demos:
                st.page_link(page, label=label, icon=icon)
        
        # Settings Section
        st.subheader("Settings")
        if "Administrator" in module_list:
            st.page_link("pages/app_users.py", label="Users", icon=":material/settings_account_box:")
            st.page_link("pages/app_user_group.py", label="User Group", icon=":material/group:")
        
        
        st.page_link("pages/app_profile.py", label="Profile", icon=":material/manage_accounts:")
        

        # Sign out button
        if st.button(":material/exit_to_app: Sign out", type="secondary"):
            st.cache_data.clear()
            st.cache_resource.clear()
            st.session_state.clear()
            st.rerun()

def get_login():
    """
    Handle the login process and render the appropriate menu.
    """
    if all(k in st.session_state for k in ["username", "user", "user_id", "modules", "chat-history", "chat-save"]):
        get_menu(st.session_state["modules"], st.session_state["user"])
        return True
    else:
        # Login Form
        with st.form('form-login'):
            st.subheader(":red[Oracle AI] Data Platform")
            col1, col2 = st.columns(2)
            with col1:
                st.image("images/st_login.gif")
                st.markdown(
                    ":gray-badge[:material/smart_toy: Agents] "
                    ":gray-badge[:material/database: Autonomous 23ai] "
                    ":gray-badge[:material/database_search: Select AI] "
                    ":gray-badge[:material/plagiarism: Select AI RAG] "
                    ":gray-badge[:material/psychology: Generative AI] "
                    ":gray-badge[:material/mic: STT RealTime] "
                    ":gray-badge[:material/description: Document Understanding] "
                    ":gray-badge[:material/privacy_tip: PII Detection] "
                )
            with col2:                
                username = st.text_input('Username')
                password = st.text_input('Password', type='password')
                # Selectbox: Laguage
                language = st.selectbox(
                    "Language",
                    options=("Spanish", "Portuguese", "English")
                )
                language_message = None
                match language:
                    case "Spanish":
                        language_message = "No tengo esa información."
                    case "Portuguese":
                        language_message = "Não tenho essa informação."
                    case "English":
                        language_message = "I don't have that information."

                btn_login = st.form_submit_button('Login', type='primary')

            if btn_login:
                df = db_user_service.get_access(username, password)

                if df is not None and not df.empty:
                    user_state = df['USER_STATE'].iloc[0]

                    # Check if user is deactivate
                    if user_state == 1:
                        # Set session state
                        st.session_state.update({
                            'user_id'            : int(df['USER_ID'].iloc[0]),
                            'user_group_id'     : int(df['USER_GROUP_ID'].iloc[0]),
                            'modules'            : df['MODULE_NAMES'].iloc[0],
                            'username'           : df['USER_USERNAME'].iloc[0],
                            'user'               : f"{df['USER_NAME'].iloc[0]}, {df['USER_LAST_NAME'].iloc[0]}",
                            'language'           : language,
                            'language-message'   : language_message,
                            'chat-select-ai'     : [],
                            'chat-select-ai-rag' : [],
                            'chat-docs'          : [],
                            'chat-save'          : [],
                            'chat-modules'       : [],
                            'chat-objects'       : [],
                            'chat-agent'         : 0,
                            'chat-history'       : []
                        })
                        st.switch_page("app.py")
                        st.rerun()
                    
                    else:
                        st.error("This user is deactivated.", icon=":material/gpp_maybe:")
                
                else:
                    st.error("Invalid username or password", icon=":material/gpp_maybe:")
        
        return False