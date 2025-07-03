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
                A.USER_GROUP_ID,
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
                        
                        SELECT 'Vector Database' AS MODULE_NAME,
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
                A.USER_GROUP_ID,
                B.USER_GROUP_NAME,
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
            JOIN USER_GROUP B
                ON A.USER_GROUP_ID = B.USER_GROUP_ID
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
            user_group_id,
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
            user_group_id(int) : The ID of the user group.
            username (str)     : Username of the user.
            password (str)     : Password of the user.
            name (str)         : First name of the user.
            last_name (str)    : Last name of the user.
            email (str)        : Email address of the user.
            modules (str)      : JSON string of user modules.

        Returns:
            str: A message indicating the result of the operation.
        """
        query = """
            SELECT USER_ID, USER_STATE
            FROM USERS
            WHERE USER_USERNAME = :username
        """
        df = pd.read_sql(query, con=self.conn, params={"username": username})

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
                return f"User '{username}' already exists and is active.", int(user_id)
        else:
            with self.conn.cursor() as cur:
                user_id_var = cur.var(int)  # Define the output variable
                cur.execute(f"""
                    INSERT INTO USERS (                        
                        USER_GROUP_ID,
                        USER_USERNAME,
                        USER_PASSWORD,
                        USER_SEL_AI_PASSWORD,
                        USER_NAME,
                        USER_LAST_NAME,
                        USER_EMAIL,
                        USER_MODULES
                    ) VALUES (
                        '{user_group_id}',
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
            user_group_id,
            username,
            name,
            last_name,
            email,
            state,
            modules  # <- nuevo parámetro
        ):
        """
        Updates user information in the database.

        Args:
            user_id (int)       : The ID of the user to update.
            user_group_id (int) : The ID of the user group.
            username (str)      : Updated username.
            name (str)          : Updated first name.
            last_name (str)     : Updated last name.
            email (str)         : Updated email address.
            state (int)         : Updated user state.

        Returns:
            str: A message indicating success.
        """
        with self.conn.cursor() as cur:
            cur.execute(f"""
                UPDATE USERS SET 
                    USER_GROUP_ID  = {user_group_id},
                    USER_USERNAME  = '{username}',
                    USER_NAME      = '{name}',
                    USER_LAST_NAME = '{last_name}',
                    USER_EMAIL     = '{email}',
                    USER_STATE     = {state},
                    USER_MODULES   = '{modules}'
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
        Deletes user and all related records in the correct order to avoid FK constraint violations.
        """
        with self.conn.cursor() as cur:

            # 1. Obtener agent_ids relacionados al usuario
            cur.execute("""
                SELECT agent_id FROM agent_user WHERE user_id = :user_id
            """, {"user_id": user_id})
            agent_ids = [row[0] for row in cur.fetchall()]

            # 2. Eliminar relaciones en AGENT_USER (solo las del usuario)
            cur.execute("""
                DELETE FROM agent_user WHERE user_id = :user_id
            """, {"user_id": user_id})

            # 3. Eliminar AGENTS si ya no tienen más relaciones en AGENT_USER
            if agent_ids:
                cur.execute(f"""
                    DELETE FROM agents
                    WHERE agent_id IN ({','.join(map(str, agent_ids))})
                    AND NOT EXISTS (
                        SELECT 1 FROM agent_user WHERE agent_id = agents.agent_id
                    )
                """)

            # 4. Obtener file_ids relacionados al usuario
            cur.execute("""
                SELECT file_id FROM file_user WHERE user_id = :user_id
            """, {"user_id": user_id})
            file_ids = [row[0] for row in cur.fetchall()]

            # 5. Eliminar relaciones en FILE_USER (solo las del usuario)
            cur.execute("""
                DELETE FROM file_user WHERE user_id = :user_id
            """, {"user_id": user_id})

            # 6. Eliminar DOCS de archivos si ya no están relacionados a ningún usuario
            if file_ids:
                cur.execute(f"""
                    DELETE FROM docs
                    WHERE file_id IN ({','.join(map(str, file_ids))})
                    AND NOT EXISTS (
                        SELECT 1 FROM file_user WHERE file_id = docs.file_id
                    )
                """)

                # 7. Eliminar FILES si ya no están asociados a ningún usuario
                cur.execute(f"""
                    DELETE FROM files
                    WHERE file_id IN ({','.join(map(str, file_ids))})
                    AND NOT EXISTS (
                        SELECT 1 FROM file_user WHERE file_id = files.file_id
                    )
                """)

            # 8. Eliminar al usuario
            cur.execute("""
                DELETE FROM users WHERE user_id = :user_id
            """, {"user_id": user_id})

        self.conn.commit()

        return f"User :green[{username}] has been deleted successfully."

    
    def get_all_user_group_cache(self, force_update=False):
        if force_update:
            # Borra la caché de la función
            self.get_all_user_group.clear()
        return self.get_all_user_group()

    @st.cache_data
    def get_all_user_group(_self):
        """
        Retrieves all active modules from the database for user.

        Args:
            user_id (int): The ID of the user.
        
        Returns:
            pd.DataFrame: A DataFrame containing module information.
        """
        query = f"""
            SELECT
                A.USER_GROUP_ID,
                A.USER_GROUP_NAME,
                A.USER_GROUP_DESCRIPTION,
                A.USER_GROUP_STATE,
                A.USER_GROUP_DATE
            FROM
                USER_GROUP A
            WHERE
                A.USER_GROUP_STATE = 1
        """
        return pd.read_sql(query, con=_self.conn)

    def get_all_user_group_cache(self, force_update=False):
        """
        Cached wrapper to retrieve users from the same user group excluding self.
        """
        if force_update:
            self.get_all_user_group.clear()
        return self.get_all_user_group()

    @st.cache_data
    def get_all_user_group(_self):
        """
        Retrieves all user groups with user count.
        """
        query = """
            SELECT
                A.USER_GROUP_ID,
                A.USER_GROUP_NAME,
                A.USER_GROUP_DESCRIPTION,
                A.USER_GROUP_STATE,
                A.USER_GROUP_DATE,
                (
                    SELECT COUNT(*) FROM USERS U 
                    WHERE U.USER_GROUP_ID = A.USER_GROUP_ID
                    AND U.USER_STATE <> 0
                ) AS USER_COUNT
            FROM USER_GROUP A
            ORDER BY A.USER_GROUP_ID DESC
        """
        return pd.read_sql(query, con=_self.conn)
    
    def insert_user_group(self, user_group_name, user_group_description):
        query = """
            INSERT INTO user_group (
                user_group_name,
                user_group_description
            ) VALUES (
                :name,
                :description
            )
            RETURNING user_group_id INTO :new_id
        """
        with self.conn.cursor() as cur:
            new_id = cur.var(int)
            cur.execute(query, {
                "name": user_group_name,
                "description": user_group_description,
                "new_id": new_id
            })
            self.conn.commit()
            user_group_id = new_id.getvalue()

            if isinstance(user_group_id, list):
                user_group_id = user_group_id[0]

        return f"User Group '{user_group_name}' created successfully.", int(user_group_id)

    def update_user_group(self, user_group_id, user_group_name, user_group_description, user_group_state):
        query = """
            UPDATE user_group
            SET 
                user_group_name = :name,
                user_group_description = :description,
                user_group_state = :state
            WHERE user_group_id = :id
        """
        with self.conn.cursor() as cur:
            cur.execute(query, {
                "name": user_group_name,
                "description": user_group_description,
                "state": user_group_state,
                "id": user_group_id
            })
        self.conn.commit()
        return f"User Group '{user_group_name}' updated successfully."

    def delete_user_group(self, user_group_id):
        query = """
            DELETE FROM USER_GROUP
            WHERE USER_GROUP_ID = :user_group_id
        """
        with self.conn.cursor() as cur:
            cur.execute(query, {"user_group_id": user_group_id})
        self.conn.commit()
        return f"User Group ID '{user_group_id}' has been deleted successfully."


    def get_all_user_group_shared_cache(self, user_id, force_update=False):
        if force_update:
            self.get_all_user_group_shared.clear()
        return self.get_all_user_group_shared(user_id)

    @st.cache_data
    def get_all_user_group_shared(_self, user_id):
        query = f"""
            SELECT
                A.USER_ID,
                A.USER_GROUP_ID,
                B.USER_GROUP_NAME,
                A.USER_USERNAME,
                A.USER_NAME || ' ' || A.USER_LAST_NAME AS USER_FULL_NAME,
                A.USER_EMAIL,
                A.USER_STATE,
                A.USER_DATE
            FROM
                USERS A
            JOIN USER_GROUP B
                ON A.USER_GROUP_ID = B.USER_GROUP_ID
            WHERE
                A.USER_STATE <> 0
                AND A.USER_ID <> {user_id}
                AND A.USER_GROUP_ID = (
                    SELECT USER_GROUP_ID FROM USERS WHERE USER_ID = {user_id}
                )
            ORDER BY A.USER_ID DESC
        """
        return pd.read_sql(query, con=_self.conn)