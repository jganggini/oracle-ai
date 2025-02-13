import streamlit as st
import pandas as pd
from app_call import app_call
from app_chat import app_chat

# app_call
if 'transcription_text' not in st.session_state:
    st.session_state['transcription_text'] = ''
if 'transcription_text_news' not in st.session_state:
    st.session_state['transcription_text_news'] = ''
if 'transcription_html' not in st.session_state:
    st.session_state['transcription_html'] = ''
if 'update_count' not in st.session_state:
    st.session_state['update_count'] = 0
if 'call_sentiments_sentence_metric' not in st.session_state:
    st.session_state['call_sentiments_sentence_metric'] = ''
if 'sentiments_sentence_score' not in st.session_state:
    st.session_state['sentiments_sentence_score'] = ''
if 'sentiments_sentence' not in st.session_state:
    st.session_state['sentiments_sentence'] = ''
if 'sentiments_aspect' not in st.session_state:
    st.session_state['sentiments_aspect'] = ''
if 'previous_sentiment_score' not in st.session_state:
    st.session_state['previous_sentiment_score'] = 0.0
if 'df_customer' not in st.session_state:
    st.session_state.df_customer = pd.DataFrame()

# app_chat
if 'filtered_calls_date' not in st.session_state:
    st.session_state['filtered_calls_date'] = ''
if 'selected_calls_date' not in st.session_state:
    st.session_state['selected_calls_date'] = ''

# Streamlit app configuration
st.set_page_config(
        page_title="AI Assistant | Oracle Cloud",
        page_icon="🅾️",
        layout="wide",
        initial_sidebar_state="expanded"
    )

pages = {
    "Menu": [
        st.Page(app_call, title="AI Assistant"),
        st.Page(app_chat, title="Chatbot")
    ]
}

pg = st.navigation(pages)
pg.run()

# pip install -r requirements.txt
# conda activate stt
# streamlit run app.py --server.port 8503
# conda pack -n stt -o stt_env.tar.gz
# https://acortar.link/oci_data_ai