import streamlit as st

def get_toast(msg: str, icon: str = ":material/info:"):
    """
    Displays a reusable toast notification in Streamlit.

    Args:
        msg (str): The message to display in the toast.
        icon (str): The icon to display alongside the message (Streamlit format).
                    Default is ":material/info:".
    """
    st.toast(msg, icon=icon)