import streamlit as st
import pandas as pd
from services.database.connection import Connection

class FileService:
    """
    Service class for handling all operations related to files (FILES).
    """
    def __init__(self):
        """
        Initializes the FileService with a shared database connection instance.
        """
        self.conn_instance = Connection()
        self.conn = self.conn_instance.get_connection()

    def get_all_files_cache(self, user_id, force_update=False):
        if force_update:
            # Borra la caché de la función
            self.get_all_files.clear()
        return self.get_all_files(user_id)

    @st.cache_data
    def get_all_files(_self, user_id):
        """
        Retrieves all files associated with a user, excluding deactivated files.

        Args:
            user_id (int): The ID of the user.

        Returns:
            pd.DataFrame: A DataFrame containing file information.
        """
        query = f"""
            SELECT 
                A.FILE_ID,
                A.USER_ID,
                A.MODULE_ID,
                B.MODULE_NAME,
                A.FILE_SRC_FILE_NAME,
                A.FILE_SRC_SIZE,
                A.FILE_SRC_STRATEGY,
                CASE 
                    WHEN B.MODULE_VECTOR_STORE=0 THEN NULL 
                    ELSE FILE_TRG_OBJ_NAME 
                END AS FILE_TRG_OBJ_NAME,
                A.FILE_TRG_TOT_PAGES,
                A.FILE_TRG_TOT_CHARACTERS,
                A.FILE_TRG_TOT_TIME,
                A.FILE_TRG_LANGUAGE,
                A.FILE_TRG_PII,
                A.FILE_VERSION,
                A.FILE_DATE,
                A.FILE_STATE
            FROM FILES A
            LEFT JOIN MODULES B
                ON B.MODULE_ID = A.MODULE_ID
            WHERE
                A.USER_ID = '{user_id}' 
                AND A.FILE_STATE <> 0
            ORDER BY
                A.FILE_ID DESC
        """
        return pd.read_sql(query, con=_self.conn)

    def insert_file(
            self,
            file_name,
            user_id,
            module_id,
            file_src_file_name,
            file_src_size,
            file_src_strategy,
            file_trg_obj_name,
            file_trg_language,
            file_trg_pii
        ):
        """
        Inserts or updates a file record in the database and returns the file_id.

        Args:
            file_name (str)           : Name of the file.
            user_id (int)             : ID of the user.
            module_id (int)           : ID of the module.
            file_src_file_name (str)  : Source file name.
            file_src_size (int)       : Size of the source file.
            file_src_strategy (str)   : Strategy for the source file.
            file_trg_obj_name (str)   : Target object name.
            file_trg_pii (int)        : PII (Personally Identifiable Information) flag.

        Returns:
            tuple: A message and the file_id.
        """
        # Check if the file already exists
        check_query = f"""
            SELECT
                FILE_ID,
                FILE_VERSION,
                FILE_STATE
            FROM
                FILES
            WHERE
                FILE_SRC_FILE_NAME = '{file_src_file_name}'
                AND USER_ID = {user_id}
                AND FILE_TRG_PII = {file_trg_pii}
        """
        df = pd.read_sql(check_query, con=self.conn)

        if not df.empty:
            file_id = df['FILE_ID'].iloc[0]
            file_version = df['FILE_VERSION'].iloc[0]

            # Update the existing file record
            with self.conn.cursor() as cur:
                cur.execute(f"""
                    UPDATE FILES SET
                        FILE_SRC_SIZE      = '{file_src_size}',
                        FILE_SRC_STRATEGY  = '{file_src_strategy}',
                        FILE_TRG_LANGUAGE  = '{file_trg_language}',
                        FILE_VERSION       = {file_version} + 1,
                        FILE_STATE         = 1,
                        FILE_DATE          = SYSDATE
                    WHERE FILE_ID = {file_id}
                """)
            self.conn.commit()

            # Delete documents
            with self.conn.cursor() as cur:
                cur.execute(f"""
                    DELETE FROM DOCS WHERE FILE_ID = {file_id}
                """)
            self.conn.commit()

            return f"File '{file_name}' already existed and adding new version.", file_id

        else:
            # Insert a new file record
            with self.conn.cursor() as cur:
                file_id_var = cur.var(int)  # Define the output variable
                cur.execute(f"""
                    INSERT INTO FILES (
                        USER_ID,
                        MODULE_ID,
                        FILE_SRC_FILE_NAME,
                        FILE_SRC_SIZE,
                        FILE_SRC_STRATEGY,
                        FILE_TRG_OBJ_NAME,
                        FILE_TRG_PII
                    ) VALUES (
                        {user_id},
                        {module_id},
                        '{file_src_file_name}',
                        '{file_src_size}',
                        '{file_src_strategy}',
                        '{file_trg_obj_name}',
                        '{file_trg_pii}'
                    ) RETURNING FILE_ID INTO :file_id
                """, {"file_id": file_id_var})
            self.conn.commit()
            return f"File '{file_name}' has been created successfully.", file_id_var.getvalue()[0]
    
    def update_extraction(
            self,
            file_id,
            file_trg_extraction
        ):
        """
        Updates the file extraction information in the database using CLOB for large text.

        Args:
            file_id (int)             : ID of the file to update.
            file_trg_extraction (str) : Extraction content to update.

        Returns:
            str: Success message or error message.
        """
        # Define chunk size for splitting the content
        chunk_size     = 4000  # Oracle supports up to 4000 characters per chunk
        tot_characters = len(file_trg_extraction)
        for i in range(0, tot_characters, chunk_size):
            chunk = file_trg_extraction[i:i + chunk_size]

            with self.conn.cursor() as cur:
                # Append the current chunk to the CLOB column
                cur.execute(f"""
                    UPDATE FILES SET
                        FILE_TRG_EXTRACTION     = CONCAT(FILE_TRG_EXTRACTION,'{chunk.replace("'", "''")}')
                    WHERE FILE_ID = {file_id}
                """)
            self.conn.commit()

        return f"File extraction has been updated successfully."

    def update_file(
            self,
            file_id,
            file_trg_obj_name,
            file_trg_tot_pages,
            file_trg_tot_characters,
            file_trg_tot_time,
            file_trg_language
        ):
        """
        Updates the file information in the database.

        Args:
            file_id (int)                 : ID of the file to update.
            file_trg_obj_name (str)       : Target object name.
            file_trg_extraction (str)     : Extraction content to update.
            file_trg_tot_pages (int)      : Total number of pages.
            file_trg_tot_characters (int) : Total number of characters.
            file_trg_tot_time (str)       : Total processing time.
            file_trg_language (str)       : Language of the file.

        Returns:
            str: Success message or error message.
        """
        # Update the existing file record
        with self.conn.cursor() as cur:
            cur.execute(f"""
                UPDATE FILES SET
                    FILE_TRG_OBJ_NAME       = '{file_trg_obj_name}',
                    FILE_TRG_TOT_PAGES      = {file_trg_tot_pages},
                    FILE_TRG_TOT_CHARACTERS = {file_trg_tot_characters},
                    FILE_TRG_TOT_TIME       = '{file_trg_tot_time}',
                    FILE_TRG_LANGUAGE       = '{file_trg_language}'
                WHERE FILE_ID = {file_id}
            """)
        self.conn.commit()
        return f"The file was updated successfully."


    def delete_file(
            self,
            file_name,
            file_id
        ):
        """
        Deletes or deactivates a file object in the database.

        Args:
            file_name (str) : Name of the file to delete.
            file_id (int)   : ID of the file to delete.

        Returns:
            str: Success or error message.
        """
        query = f"""
            SELECT
                FILE_ID
            FROM FILES
            WHERE FILE_ID = {file_id}
                AND FILE_STATE<>0
        """
        df = pd.read_sql(query, con=self.conn)

        if not df.empty:
            with self.conn.cursor() as cur:
                cur.execute(f"""
                    UPDATE FILES SET
                        FILE_STATE = 0,
                        FILE_DATE  = SYSDATE
                    WHERE FILE_ID = {file_id}
                """)
            self.conn.commit()
            return f"File '{file_name}' has been deleted successfully."
        else:
            return f"File '{file_name}' does not exist or is already deactivated."