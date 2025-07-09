import oci
import re
import os
import time
import random
import string
import base64
import pandas as pd
import streamlit as st
from graphviz import Digraph
from typing import List, Tuple
from dotenv import load_dotenv

# Para ChatMessages
from langchain.schema import HumanMessage, AIMessage

load_dotenv()

class FunctionService:
    """
    Class:
    """

    @staticmethod
    def get_list_to_str(input: str) -> list:
        return [elem.strip() for elem in input.split(",")]
    
    @staticmethod
    def get_password() -> str:
        """Genera una contraseña de longitud fija con, al menos, un dígito."""
        length = 16
        allowed_chars = (
            string.ascii_uppercase +  # A-Z
            string.ascii_lowercase +  # a-z
            string.digits +           # 0-9
            "!@#$^&*+-.,{}[]():?<>_"  # Símbolos
        )
        while True:
            password = "".join(random.choices(allowed_chars, k=length))
            # Verifica si tiene al menos un dígito
            if any(ch.isdigit() for ch in password):
                return password
    
    @staticmethod
    def get_valid_url_path(file_name: str) -> str:
        config = oci.config.from_file(profile_name=os.getenv('CON_OCI_PROFILE_NAME', 'DEFAULT'))
        region = config["region"]
        
        return (
            f"https://objectstorage.{region}.oraclecloud.com/"
            f"n/{os.getenv('CON_ADB_BUK_NAMESPACENAME')}/"
            f"b/{os.getenv('CON_ADB_BUK_NAME')}/o/{file_name}"
        )

    @staticmethod
    def get_changes_to_df(original_df: pd.DataFrame, edited_df: pd.DataFrame, compare_cols: list) -> pd.DataFrame:
        mask_changed = (original_df[compare_cols] != edited_df[compare_cols]) & (~edited_df[compare_cols].isna())
        rows_changed = mask_changed.any(axis=1)
        # Devolver las filas completas del edited_df, no sólo las columnas comparadas
        return edited_df[rows_changed]

    @staticmethod
    def get_valid_table_name(schema: str, file_name: str) -> str:
        # Reemplazar 'admin' con el valor de la variable de entorno si aplica
        if schema.lower() == "sel_ai_user_id_0":
            schema = os.getenv('CON_ADB_DEV_USER_NAME')

        # Extraer la parte final del nombre del archivo, en caso de que venga con ruta
        base_name = file_name.split('/')[-1]
        
        # Quitar la extensión, si existe
        extension_index = base_name.rfind('.')
        if extension_index != -1:
            base_name = base_name[:extension_index]
        
        # Convertir a mayúsculas
        base_name = base_name.upper()
        
        # Reemplazar los caracteres no permitidos por '_'
        base_name = re.sub(r'[^A-Z0-9_]', '_', base_name)
        
        # Truncar a un máximo de 30 caracteres
        base_name = base_name[:30]
        
        return (f"{schema}.{base_name}").lower()
    
    @staticmethod
    def get_csv_column_comments(uploaded_file) -> pd.DataFrame:
        # Read the CSV file to extract the header
        df = pd.read_csv(uploaded_file, nrows=0)  # Only read the header
        columns = df.columns.tolist()  # Get the list of column names
        
        # Prepare data for the editor (initialize comments as empty strings)
        return pd.DataFrame({
            "Column Name": columns,
            "Comment": ["" for _ in columns]
        })
    
    @staticmethod
    def get_tables_json(df, group_by_columns, fields):
        data = {}

        for _, row in df.iterrows():
            # Construir la clave principal basada en las columnas de agrupación
            group_key = ".".join(str(row[col]) for col in group_by_columns)

            if group_key not in data:
                data[group_key] = []

            # Crear el diccionario para los campos
            item = {field_name: row[col_name] for field_name, col_name in fields.items()}
            
            data[group_key].append(item)

        return data
    
    @staticmethod
    def get_tables_dot(data):
        dot = Digraph()

        # Configuración de colores
        dot.attr(bgcolor="#101414")
        dot.attr("node", fontcolor="white", fontsize="11")
        dot.attr("edge", color="#403c44")

        for table_name, columns in data.items():
            # Crear tabla usando HTML-like labels con estilos personalizados
            table_html = f"<<TABLE BORDER='1' CELLBORDER='1' CELLSPACING='0' BGCOLOR='#101414' COLOR='#403c44'>"
            table_html += f"<TR><TD COLSPAN='2' BGCOLOR='#403c44' ALIGN='CENTER'><FONT FACE='Arial' COLOR='white'><B>{table_name}</B></FONT></TD></TR>"
            table_html += "".join(
                [f"<TR><TD><FONT FACE='Arial' COLOR='white'>{col['column_name']}</FONT></TD><TD><FONT FACE='Arial' COLOR='white'>{col['data_type']}</FONT></TD></TR>" for col in columns]
            )
            table_html += "</TABLE>>"

            dot.node(table_name, label=table_html, shape="plaintext")

        return dot
    
    @staticmethod
    def track_time(control):
        """
        Tracks the total time elapsed between start and stop events for each user session.

        Args:
            control (int): 1 to start the timer, 0 to stop the timer and return elapsed time.

        Returns:
            str: Elapsed time in 'HH:MM:SS' format if control is 0.
        """
        if control == 1:  # Start the timer
            st.session_state.start_time = time.time()
            return "00:00:00"
        elif control == 0:  # Stop the timer and calculate elapsed time
            if "start_time" not in st.session_state:
                return "Timer was not started. Use control = 1 to start the timer."
            
            elapsed_time = int(time.time() - st.session_state.start_time)
            hours = elapsed_time // 3600
            minutes = (elapsed_time % 3600) // 60
            seconds = elapsed_time % 60
            return f"{hours:02}:{minutes:02}:{seconds:02}"
        else:
            return "Invalid control value. Use 1 to start and 0 to stop."
    
    @staticmethod
    def get_name_from_path(path: str) -> str:
        """
        Devuelve el nombre del archivo si la ruta apunta a un archivo o contiene una extensión,
        o el nombre de la carpeta si la ruta es un directorio.
        Si la ruta no es válida, devuelve "unknown".

        Args:
            path (str): La ruta completa (puede ser un archivo o un directorio).

        Returns:
            str: El nombre del archivo o carpeta, o "unknown" si la ruta no es válida.
        """
        if path and "." in os.path.basename(path):
            # Si contiene una extensión, devuelve el nombre del archivo
            return os.path.basename(path)
        elif os.path.isdir(path):
            # Si es un directorio, devuelve el nombre del directorio
            return os.path.basename(os.path.normpath(path))
        else:
            # Si la ruta no es válida, devuelve "unknown"
            return "unknown"
        
    @staticmethod
    def is_valid_password(password):
        """
        Validate the password based on common Oracle requirements.

        Args:
            password (str): The password to validate.

        Returns:
            bool: True if the password is valid, False otherwise.
        """
        if not password or len(password) < 8:  # Longitud mínima de 8 caracteres
            return False
        if not any(char.isupper() for char in password):  # Al menos una mayúscula
            return False
        if not any(char.islower() for char in password):  # Al menos una minúscula
            return False
        if not any(char.isdigit() for char in password):  # Al menos un número
            return False
        if not any(char in "!@#$%^&*()-_+=" for char in password):  # Al menos un caracter especial
            return False
        return True

    @staticmethod
    def encode_images_to_base64(image_path):
        """
        Encodes images in a specified directory to base64 strings.

        Args:
            image_path (str): Path to the directory containing image files.

        Returns:
            List[str]: List of base64-encoded image strings.
        """
        image_files = [
            os.path.join(image_path, f) 
            for f in os.listdir(image_path) 
            if f.endswith((".png", ".jpg", ".jpeg", ".bmp"))
        ]

        base64_images = []
        for image_file in image_files:
            with open(image_file, "rb") as img_file:
                encoded = base64.b64encode(img_file.read()).decode("utf-8")
                base64_images.append(encoded)

        return base64_images
    
    @staticmethod
    def encode_bytes_to_base64(image_bytes):
        """
        Encodes a single byte object (representing an image) to a base64 string.

        Args:
            image_bytes (bytes): Image data in bytes format.

        Returns:
            str: Base64-encoded image string.
        """
        if not image_bytes:  # Verifica si es None o está vacío
            return ""

        if not isinstance(image_bytes, bytes):
            raise ValueError(f"Invalid input type: Expected bytes, got {type(image_bytes)}")
        
        return base64.b64encode(image_bytes).decode("utf-8")
    
    @staticmethod
    def build_langchain_messages_from_qa(rag_history):
        """
        Convierto la lista de (user_question, bot_answer) en
        una lista [HumanMessage(...), AIMessage(...), ...]
        para pasársela a 'history' en el prompt.
        """
        messages = []
        for user_q, bot_a in rag_history:
            messages.append(HumanMessage(content=user_q))
            messages.append(AIMessage(content=bot_a))
        return messages
    
    @staticmethod
    def parse_srt_blocks(srt_text: str) -> List[Tuple[str, str, str]]:
        """
        Parsea bloques de SRT sin asumir cantidad fija de líneas.
        Retorna una lista de tuplas (index, timestamp, texto).
        """
        blocks = []
        raw_blocks = srt_text.strip().split("\n\n")
        
        for block in raw_blocks:
            lines = block.strip().split("\n")
            if len(lines) >= 2:
                idx = lines[0].strip()
                ts = lines[1].strip()
                txt = "\n".join(line.strip() for line in lines[2:]).strip()
                blocks.append((idx, ts, txt))
        return blocks
    
    @staticmethod
    def normalize_obfuscated_email(text: str) -> str:
        # Reemplaza "arroba" y "punto"
        text = re.sub(r"\barroba\b", "@", text, flags=re.IGNORECASE)
        text = re.sub(r"\bpunto\b", ".", text, flags=re.IGNORECASE)

        # Elimina espacios alrededor de @ y .
        text = re.sub(r"\s*@\s*", "@", text)
        text = re.sub(r"\s*\.\s*", ".", text)

        # Limpia espacios múltiples (opcional)
        text = re.sub(r"\s+", " ", text)

        return text
    
    