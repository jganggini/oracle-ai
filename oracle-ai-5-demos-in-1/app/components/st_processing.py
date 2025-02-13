import time
import base64
import streamlit as st

def get_processing(visible: bool, image_path: str = "images/st_processing.gif", seg: int = 5):
    """
    Displays or hides a loading overlay with an optional animated image.

    Args:
        visible (bool): If True, displays the overlay. If False, hides it.
        image_path (str): Path to the image to display in the overlay (optional).
    """
    if visible:
        # Convert the image to base64
        with open(image_path, "rb") as img_file:
            image_base64 = base64.b64encode(img_file.read()).decode()
        
        st.markdown(
            f"""
            <style>
                .processing {{
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background-color: rgba(0, 0, 0, 0.4); /* Fondo semitransparente */
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    z-index: 100;
                }}
                .processing img {{
                    position: fixed;
                    bottom: 60px;
                    right: 15px;
                    max-width: 150px;
                    max-height: 150px;
                }}
            </style>
            <div class="processing">
                <img src="data:image/gif;base64,{image_base64}" alt="Loading...">
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        time.sleep(seg)
        st.markdown(
            """
            <style>
                .processing {
                    display: none;
                }
            </style>
            """,
            unsafe_allow_html=True,
        )
        st.rerun()