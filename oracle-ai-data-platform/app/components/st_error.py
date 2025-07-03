import streamlit as st

def get_error(msg: str, icon: str = ":material/error:"):
    """
    Displays a reusable error toast in Streamlit.

    Args:
        msg (str): The message to display in the toast.
        icon (str): The icon to display alongside the message (Streamlit format).
                    Default is ":material/error:".
    """
    st.error(msg, icon=icon)
    print(msg)