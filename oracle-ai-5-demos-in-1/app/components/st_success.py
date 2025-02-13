import time
import streamlit as st

def get_success(msg: str, icon: str = ":material/network_intelligence_update:"):
    """
    Displays a reusable success toast in Streamlit.

    Args:
        msg (str): The message to display in the toast.
        icon (str): The icon to display alongside the message (Streamlit format).
                    Default is ":material/network_intelligence_update:".
    """
    st.success(msg, icon=icon)
    time.sleep(1)