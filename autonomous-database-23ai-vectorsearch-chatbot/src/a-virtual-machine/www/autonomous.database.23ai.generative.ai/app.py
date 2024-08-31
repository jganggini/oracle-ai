import streamlit as st
from app_chat import app_chat
from app_elt import app_elt

# Streamlit app configuration
st.set_page_config(
        page_title="Autonomous Database 23AI",
        page_icon="🅾️",
        layout="centered",
        initial_sidebar_state="expanded"
    )

pages = {
    "Autonomous Database 23ai": [
        st.Page(app_chat, title="Chatbot"),
        st.Page(app_elt, title="Generate Data")
    ]
}

pg = st.navigation(pages)
pg.run()

# https://docs.streamlit.io/develop/tutorials/llms/build-conversational-apps
# 
# pip install -r requirements.txt
# streamlit run app.py --server.port 8501