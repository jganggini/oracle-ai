import streamlit as st

def get_footer():
    """
    Displays a fixed footer at the bottom of the Streamlit app with custom styling.

    The footer includes text, a background color, and a hyperlink to a profile.
    """
    st.markdown(
        """
        <style>
            .footer {
                position: fixed;
                bottom: 0;
                left: 0;
                width: 100%;
                background-color: #3a3b46; /* Color de fondo */
                color: white; /* Color del texto */
                text-align: right;
                font-size: 14px;
                padding: 10px 10px;
                z-index: 300;
            }

            .footer a {
                text-decoration: none;
                color: #97d4ec;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )
    
    # Footer content
    st.markdown(
        "<div class='footer'>Made with 🤍 in Oracle AI · Powered by <a href='https://pe.linkedin.com/in/jganggini' target='_blank'>Joel Ganggini</a></div>",
        unsafe_allow_html=True,
    )