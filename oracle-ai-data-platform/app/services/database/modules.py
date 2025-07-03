import streamlit as st
import pandas as pd
from services.database.connection import Connection

class ModuleService:
    """
    Service class for handling all operations related to modules.
    """

    def __init__(self):
        """
        Initializes the ModuleService with a shared database connection instance.
        """
        self.conn_instance = Connection()
        self.conn = self.conn_instance.get_connection()

    @st.cache_data
    def get_all_modules(_self):
        """
        Retrieves all active modules from the database.

        Returns:
            pd.DataFrame: A DataFrame containing module information.
        """
        query = f"""
            SELECT 
                M.MODULE_ID,
                M.MODULE_NAME,
                M.MODULE_FOLDER,
                M.MODULE_SRC_TYPE,
                M.MODULE_TRG_TYPE
            FROM
                MODULES M
            WHERE
                M.MODULE_STATE = 1
            ORDER BY M.MODULE_ID ASC
        """
        return pd.read_sql(query, con=_self.conn)

    def get_modules_cache(self, user_id, force_update=False):
        if force_update:
            self.get_modules.clear()
        return self.get_modules(user_id)

    @st.cache_data
    def get_modules(_self, user_id):
        """
        Retrieves active modules assigned to the specific user.

        Args:
            user_id (int): The user_id of the user.

        Returns:
            pd.DataFrame: A DataFrame containing MODULE_ID and MODULE_NAME.
        """
        query = f"""
            SELECT 
                M.MODULE_ID,
                M.MODULE_NAME,
                M.MODULE_FOLDER,
                M.MODULE_SRC_TYPE,
                M.MODULE_TRG_TYPE
            FROM USERS U
            JOIN JSON_TABLE(
                TO_CHAR(U.USER_MODULES),
                '$[*]' COLUMNS (
                    MODULE_ID NUMBER PATH '$'
                )
            ) JT
            ON 1=1
            JOIN MODULES M
            ON JT.MODULE_ID = M.MODULE_ID
            WHERE U.USER_ID = {user_id}
            AND M.MODULE_STATE = 1
            AND M.MODULE_ID > 0
            ORDER BY M.MODULE_ID
        """
        return pd.read_sql(query, con=_self.conn)

    
    def get_modules_files_cache(self, user_id, force_update=False):
        if force_update:
            # Borra la caché de la función
            self.get_modules_files.clear()
        return self.get_modules_files(user_id)

    @st.cache_data
    def get_modules_files(_self, user_id):
        """
        Retrieves all active modules with files assigned to a specific user.

        Args:
            user_id (int): The ID of the user.
        
        Returns:
            pd.DataFrame: A DataFrame containing module information.
        """
        query = f"""
            SELECT DISTINCT
                M.MODULE_ID,
                M.MODULE_NAME,
                F.FILE_ID,
                REPLACE(
                    REGEXP_SUBSTR(
                        REGEXP_SUBSTR(
                            F.FILE_TRG_OBJ_NAME,
                            '[^/]+$'
                        ),
                        '^[^\\.]+' 
                    ),
                '_trg','') AS OBJECT_NAME
            FROM
                MODULES M
            JOIN
                FILES F
                ON M.MODULE_ID = F.MODULE_ID
            JOIN
                FILE_USER FU
                ON F.FILE_ID = FU.FILE_ID
            WHERE
                M.MODULE_VECTOR_STORE = 1
                AND F.FILE_STATE = 1
                AND FU.USER_ID = {user_id}
        """
        return pd.read_sql(query, con=_self.conn)

    def update_agent(
            self,
            agent_id,
            user_id,
            model_id,
            agent_name,
            agent_max_out_tokens,
            agent_temperature,
            agent_top_p,
            agent_top_k,
            agent_frequency_penalty,
            agent_presence_penalty,
            agent_prompt_system,
            agent_prompt_message
        ):
        """
        Updates user information in the database.

        Args:
            agent_id (int)                  :
            user_id (int)                   : The ID of the user to update.
            model_id (int)                  :
            agent_name (str)                :
            agent_max_out_tokens (float)    :
            agent_temperature (float)       :
            agent_top_p (float)             :
            agent_top_k (float)             :
            agent_frequency_penalty (float) :
            agent_presence_penalty (float)  :
            agent_prompt_system (str)       :
            agent_prompt_message (str)      :

        Returns:
            str: A message indicating success.
        """
        query = f"""
            UPDATE AGENTS SET 
                MODEL_ID                = {model_id},
                AGENT_MAX_OUT_TOKENS    = {agent_max_out_tokens},
                AGENT_TEMPERATURE       = {agent_temperature},
                AGENT_TOP_P             = {agent_top_p},
                AGENT_TOP_K             = {agent_top_k},
                AGENT_FREQUENCY_PENALTY = {agent_frequency_penalty},
                AGENT_PRESENCE_PENALTY  = {agent_presence_penalty},
                AGENT_PROMPT_SYSTEM     = '{agent_prompt_system.replace("'", "''")}',
                AGENT_PROMPT_MESSAGE    = '{agent_prompt_message.replace("'", "''")}'
            WHERE
                AGENT_ID         = {agent_id}
                AND USER_ID      = {user_id}
        """
        with self.conn.cursor() as cur:
            cur.execute(query)
        self.conn.commit()
        return f"Agent '{agent_name}' has been updated successfully."
    

    def delete_agent(self, user_id, module_id):
        """
        Returns:
            str: A message indicating success.
        """
        query = f"""
            DELETE FROM AGENTS WHERE USER_ID = {user_id} AND MODULE_ID = {module_id}
            RETURNING AGENT_NAME INTO :agent_name
        """
        with self.conn.cursor() as cur:
            agent_name_var = cur.var(str)
            cur.execute(query, {"agent_name": agent_name_var})
        self.conn.commit()
        return f"Agent: :red[{agent_name_var.getvalue()[0]}] has been deleted successfully."