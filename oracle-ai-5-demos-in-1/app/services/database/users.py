import streamlit as st
import pandas as pd
from services.database.connection import Connection

class UserService:
    """
    Service class for managing user operations, including CRUD actions and role management.
    """

    def __init__(self):
        """
        Initializes the UserService with a shared database connection.
        """
        self.conn_instance = Connection()
        self.conn = self.conn_instance.get_connection()
    
    @st.cache_data
    def get_access(
            _self,
            username,
            password
        ):
        """
        Retrieves user information based on username and password.

        Args:
            username (str): The username of the user.
            password (str): The password of the user.

        Returns:
            pd.DataFrame: A DataFrame containing user information if valid, else empty.
        """  
        query = f"""
            SELECT
                A.USER_ID,
                A.USER_USERNAME,
                A.USER_NAME,
                A.USER_LAST_NAME,
                A.USER_EMAIL,
                A.USER_MODULES,
                (
                    SELECT JSON_ARRAYAGG(T.MODULE_NAME ORDER BY T.SORT_COL)
                    FROM (
                        SELECT M.MODULE_NAME,
                            M.MODULE_ID AS SORT_COL
                        FROM JSON_TABLE(
                                TO_CHAR(A.USER_MODULES),
                                '$[*]' COLUMNS (
                                    MODULE_ID NUMBER PATH '$'
                                )
                            ) JT
                            JOIN MODULES M 
                                ON JT.MODULE_ID = M.MODULE_ID
                        
                        UNION
                        
                        SELECT 'AI Vector Search' AS MODULE_NAME,
                            999999 AS SORT_COL  -- para forzar que vaya al final
                        FROM DUAL
                        WHERE EXISTS (
                                SELECT 1
                                FROM JSON_TABLE(
                                        TO_CHAR(A.USER_MODULES),
                                        '$[*]' COLUMNS (
                                            MODULE_ID NUMBER PATH '$'
                                        )
                                    ) JT2
                                JOIN MODULES M2
                                    ON JT2.MODULE_ID = M2.MODULE_ID
                                WHERE M2.MODULE_VECTOR_STORE = 1
                            )
                    ) T
                ) AS MODULE_NAMES,
                A.USER_STATE,
                A.USER_DATE
            FROM USERS A
            WHERE A.USER_USERNAME = '{username}' 
            AND A.USER_PASSWORD = '{password}'
        """
        return pd.read_sql(query, con=_self.conn)
    
    def get_all_users_cache(self, force_update=False):
        if force_update:
            # Borra la caché de la función
            self.get_all_users.clear()
        return self.get_all_users()

    @st.cache_data
    def get_all_users(_self):
        """
        Retrieves all active users from the database.

        Returns:
            pd.DataFrame: A DataFrame containing user information.
        """
        query = f"""
            SELECT
                A.USER_ID,
                A.USER_USERNAME,
                A.USER_PASSWORD,
                A.USER_SEL_AI_PASSWORD,
                A.USER_NAME,
                A.USER_LAST_NAME,
                A.USER_EMAIL,
                A.USER_MODULES,
                (
                    SELECT JSON_ARRAYAGG(M.MODULE_NAME ORDER BY M.MODULE_ID)
                    FROM JSON_TABLE(
                        TO_CHAR(A.USER_MODULES),
                        '$[*]' COLUMNS (
                            MODULE_ID NUMBER PATH '$'
                        )
                    ) JT
                    JOIN MODULES M
                    ON JT.MODULE_ID = M.MODULE_ID
                ) AS MODULE_NAMES,
                A.USER_STATE,
                A.USER_DATE
            FROM
                USERS A
            WHERE
                A.USER_STATE <> 0
                AND A.USER_ID > 0
            ORDER BY
                A.USER_ID DESC
        """
        return pd.read_sql(query, con=_self.conn)
    
    @st.cache_data
    def get_user(_self, user_id):
        """
        Retrieves a specific user's information by user ID.

        Args:
            user_id (int): The ID of the user.

        Returns:
            pd.DataFrame: A DataFrame containing the user's information.
        """
        query = f"""
            SELECT
                A.USER_ID,
                A.USER_USERNAME,
                A.USER_PASSWORD,
                A.USER_NAME,
                A.USER_LAST_NAME,
                A.USER_EMAIL,
                A.USER_MODULES,
                A.USER_STATE,
                A.USER_DATE
            FROM USERS A
            WHERE A.USER_ID = {user_id}
        """
        return pd.read_sql(query, con=_self.conn)

    def insert_user(
            self,
            username,
            password,
            sel_ai_password,
            name,
            last_name,
            email,
            modules
        ):
        """
        Inserts a new user into the database or reactivates an existing one.

        Args:
            username (str)  : Username of the user.
            password (str)  : Password of the user.
            name (str)      : First name of the user.
            last_name (str) : Last name of the user.
            email (str)     : Email address of the user.
            modules (str)   : JSON string of user modules.

        Returns:
            str: A message indicating the result of the operation.
        """
        query = f"""
            SELECT USER_ID, USER_STATE
            FROM USERS
            WHERE USER_USERNAME='{username}'
        """
        df = pd.read_sql(query, con=self.conn)

        if not df.empty:
            user_id       = df['USER_ID'].iloc[0]
            current_state = df['USER_STATE'].iloc[0]

            if current_state != 1:
                with self.conn.cursor() as cur:
                    cur.execute(f"""
                        UPDATE USERS 
                        SET USER_MODULES = '{modules}',
                            USER_STATE   = 1,                            
                            USER_DATE    = SYSDATE
                        WHERE USER_ID    = {user_id}
                    """)
                self.conn.commit()
                return f"User '{username}' already existed and has been reactivated.", user_id
            else:
                return f"User '{username}' already exists and is active.", user_id
        else:
            with self.conn.cursor() as cur:
                user_id_var = cur.var(int)  # Define the output variable
                cur.execute(f"""
                    INSERT INTO USERS (
                        USER_USERNAME,
                        USER_PASSWORD,
                        USER_SEL_AI_PASSWORD,
                        USER_NAME,
                        USER_LAST_NAME,
                        USER_EMAIL,
                        USER_MODULES
                    ) VALUES (
                        '{username}',
                        '{password}',
                        '{sel_ai_password}',
                        '{name}',
                        '{last_name}',
                        '{email}',
                        '{modules}'
                    ) RETURNING USER_ID INTO :user_id
                """, {"user_id": user_id_var})
            self.conn.commit()
            return f"User '{username}' has been created successfully.", user_id_var.getvalue()[0]
        
    def update_user(
            self,
            user_id,
            username,
            name,
            last_name,
            email,
            state
        ):
        """
        Updates user information in the database.

        Args:
            user_id (int)   : The ID of the user to update.
            username (str)  : Updated username.
            name (str)      : Updated first name.
            last_name (str) : Updated last name.
            email (str)     : Updated email address.
            state (int)     : Updated user state.

        Returns:
            str: A message indicating success.
        """
        with self.conn.cursor() as cur:
            cur.execute(f"""
                UPDATE USERS SET 
                    USER_USERNAME  = '{username}',
                    USER_NAME      = '{name}',
                    USER_LAST_NAME = '{last_name}',
                    USER_EMAIL     = '{email}',
                    USER_STATE     = {state}
                WHERE USER_ID      = {user_id}
            """)
        self.conn.commit()
        return f"User '{username}' has been updated successfully."
        
    def update_profile(self, user_id, username, password, name, last_name, email, state):
        """
        Updates user profile information in the database.

        Args:
            user_id (int)   : The ID of the user to update.
            username (str)  : Updated username.
            password (str)  : Updated password.
            name (str)      : Updated first name.
            last_name (str) : Updated last name.
            email (str)     : Updated email address.
            state (int)     : Updated user state.

        Returns:
            str: A message indicating success.
        """
        with self.conn.cursor() as cur:
            cur.execute(f"""
                UPDATE USERS SET 
                    USER_NAME      = '{name}',
                    USER_PASSWORD  = '{password}',
                    USER_LAST_NAME = '{last_name}',
                    USER_EMAIL     = '{email}',
                    USER_STATE     = {state}
                WHERE USER_ID      = {user_id}
            """)
        self.conn.commit()
        return f"User '{username}' has been updated successfully."
        
    def update_modules(self, user_id, modules):
        """
        Updates the modules associated with a user.

        Args:
            user_id (int)  : The username of the database.
            modules (str)  : JSON string of updated modules.

        Returns:
            str: A message indicating success.
        """
        with self.conn.cursor() as cur:
            cur.execute(f"""
                UPDATE USERS SET 
                    USER_MODULES = '{modules}'
                WHERE USER_ID    = {user_id}
            """)
        self.conn.commit()
        return f"User has been updated successfully."

    def delete_user(self, user_id, username):
        """
        
        
        Args:
            user_id (int)  : The ID of the user to deactivate.
            username (str) : The username of the user.

        Returns:
            str: A message indicating success or failure.
        """
        query = f"""
            DELETE FROM AGENTS WHERE USER_ID={user_id}
        """
        with self.conn.cursor() as cur:
            cur.execute(query)
        self.conn.commit()

        query = f"""
            DELETE FROM DOCS WHERE
            FILE_ID IN (SELECT FILE_ID FROM FILES WHERE USER_ID={user_id}) 
        """
        with self.conn.cursor() as cur:
            cur.execute(query)
        self.conn.commit()
        
        query = f"""
            DELETE FROM FILES WHERE USER_ID={user_id}
        """
        with self.conn.cursor() as cur:
            cur.execute(query)
        self.conn.commit()

        query = f"""
            DELETE FROM USERS WHERE USER_ID={user_id}
        """
        with self.conn.cursor() as cur:
            cur.execute(query)
        self.conn.commit()
        return f"User :green[{username}] has been deleted successfully."
    