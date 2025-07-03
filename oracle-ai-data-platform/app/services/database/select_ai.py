import streamlit as st
import pandas as pd
from services.database.connection import Connection

class SelectAIService:
    """
    Service class for managing Select AI operations.
    """

    def __init__(self):
        """
        Initializes the SelectAIService with a shared database connection.
        """
        self.conn_instance = Connection()
        self.conn = self.conn_instance.get_connection()

    def create_user(self, user_id, password):
        """
        Creates a new database user.

        Args:
            user_id (int): The user_id for the new database user.
            password (str): The password for the new database user.

        Returns:
            str: A message indicating success.
        """
        query = f"""
                CREATE USER SEL_AI_USER_ID_{str(user_id)}
                IDENTIFIED BY "{password}"
                DEFAULT TABLESPACE tablespace
                QUOTA UNLIMITED ON tablespace
            """
        with self.conn.cursor() as cur:
            cur.execute(query)
        self.conn.commit()

        with self.conn.cursor() as cur:
            cur.execute(f"""
                GRANT DWROLE TO SEL_AI_USER_ID_{str(user_id)}
            """)
        self.conn.commit()
        return f"[Select AI]: New User :red[SEL_AI_USER_ID_{str(user_id)}] created successfully for the database."
    
    def drop_user(self, user_id):
        """
        Deletes a database user.

        Args:
            user_id (int): The username of the database user to delete.

        Returns:
            str: A message indicating success.
        """
        try:
            query = f"""
                DROP USER SEL_AI_USER_ID_{str(user_id)} CASCADE
            """
            with self.conn.cursor() as cur:
                cur.execute(query)
            self.conn.commit()
            return f"[Select AI]: The username :red[SEL_AI_USER_ID_{str(user_id)}] of the database user to delete successfully."
        except Exception as e:
            # The username does not exist.
            if 'ORA-01918' in str(e):
                return f"[Select AI]: The username :red[SEL_AI_USER_ID_{str(user_id)}] of the database does not exist."""

    def update_user_password(self, user_id, new_password):
        """
        Updates the password of a database user.

        Args:
            user_id (int): The username of the database.
            new_password (str): The new password to set for the user.

        Returns:
            str: A message indicating the success of the operation.
        """
        with self.conn.cursor() as cur:
            cur.execute(f"""
                ALTER USER SEL_AI_USER_ID_{str(user_id)} IDENTIFIED BY "{new_password}"
            """)
        self.conn.commit()
        return f"[Select AI] The password for user was updated successfully."
    

    def update_comment(
            self,
            table_name,
            column_name,
            comment
        ):
        """
        Updates the comment for a specific column in a table.

        Args:
            table_name (str): The name of the table.
            column_name (str): The name of the column.
            comment (str): The comment to set for the column.
        """
        with self.conn.cursor() as cur:
            cur.execute(f"""
                COMMENT ON COLUMN {table_name}.{column_name} IS '{comment}'
            """)
        self.conn.commit()
    
    def create_table_from_csv(
            self,
            object_uri,
            table_name
        ):
        """
        Creates a table in the database from a CSV file.

        Args:
            object_uri (str): The URI of the CSV file.
            table_name (str): The name of the table to create.
        """    
        with self.conn.cursor() as cur:
            query = f"""
                BEGIN
                    SP_SEL_AI_TBL_CSV('{object_uri}', '{table_name}');
                END;
            """
            cur.execute(query)
        self.conn.commit()

    def create_profile(
            self,
            profile_name,
            user_id
        ):
        """
        Creates a profile for Select AI in the database.

        Args:
            profile_name (str): The name of the profile to create.
            user_id (str): The ID of the user creating the profile.
        """
        with self.conn.cursor() as cur:
            query = f"""
                BEGIN
                    SP_SEL_AI_PROFILE('{profile_name}', {user_id});
                END;
            """
            cur.execute(query)
        self.conn.commit()
    
    def get_chat(
            self,
            prompt,
            profile_name,
            action,
            language
        ):
        """
        Generates a chat response using the Select AI profile.

        Args:
            prompt (str): The user prompt or query.
            profile_name (str): The name of the profile to use.
            action (str): The action to perform.
            language (str): The language for the response.

        Returns:
            str: The generated chat response.
        """ 
        
        # Replace single quotes to avoid SQL syntax issues
        prompt = prompt.replace("'", "''")

        # Escape percentage signs to prevent formatting errors
        prompt = prompt.replace("%", "%%")
        
        # Construct the SQL query to generate the chat response
        query = f"""
            SELECT
                DBMS_CLOUD_AI.GENERATE(
                prompt       => '{prompt} /** Format the response in markdown. Do not underline titles. Just focus on the database tables. Answer in {language}. If you do not know the answer, answer imperatively and exactly: ''NNN.'' **/',
                profile_name => '{profile_name}',
                action       => '{action}') AS CHAT
            FROM DUAL
        """

        # Execute the query and return the chat response
        return pd.read_sql(query, con=self.conn)["CHAT"].iloc[0].read()
    
    def get_tables_cache(self, user_id, force_update=False):
        if force_update:
            # Borra la caché de la función
            self.get_tables.clear()
        return self.get_tables(user_id)
    
    @st.cache_data
    def get_tables(_self, user_id):        
        """
        Retrieves metadata for tables associated with the Select AI module.

        Returns:
            pd.DataFrame: A DataFrame containing table metadata, including columns and comments.
        """
        query = f"""
            SELECT 
                t.owner,
                t.table_name,
                c.column_name,
                c.data_type,
                cc.comments
            FROM 
                all_tables t
            JOIN 
                all_tab_columns c
                ON t.table_name = c.table_name AND t.owner = c.owner
            LEFT JOIN 
                all_col_comments cc
                ON c.table_name = cc.table_name 
                AND c.owner = cc.owner 
                AND c.column_name = cc.column_name
            WHERE 
                (UPPER(t.owner), UPPER(t.table_name)) IN (
                    SELECT 
                        UPPER(SUBSTR(F.FILE_TRG_OBJ_NAME, 1, INSTR(F.FILE_TRG_OBJ_NAME, '.') - 1)) AS owner,
                        UPPER(SUBSTR(F.FILE_TRG_OBJ_NAME, INSTR(F.FILE_TRG_OBJ_NAME, '.') + 1)) AS table_name
                    FROM FILES F
                    JOIN FILE_USER FU ON F.FILE_ID = FU.FILE_ID
                    WHERE 
                        F.MODULE_ID = 1 
                        AND F.FILE_STATE = 1 
                        AND FU.USER_ID = {user_id}
                )
            ORDER BY 
                t.owner, t.table_name, c.column_id
        """
        return pd.read_sql(query, con=_self.conn)