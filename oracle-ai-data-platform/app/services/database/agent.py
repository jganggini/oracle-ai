import streamlit as st
import pandas as pd
from services.database.connection import Connection

class AgentService:
    """
    Service class for handling all operations related to modules.
    """

    def __init__(self):
        """
        Initializes the ModuleService with a shared database connection instance.
        """
        self.conn_instance = Connection()
        self.conn = self.conn_instance.get_connection()

    def get_all_agents_cache(self, user_id, force_update=False):
        """
        Cached wrapper to retrieve agents assigned to specific user_id.
        """
        if force_update:
            self.get_all_agents.clear()
        return self.get_all_agents(user_id)

    @st.cache_data
    def get_all_agents(_self, user_id):
        """
        Retrieves all agents assigned to the provided user_id, with model information included.

        Args:
            user_id (int): The ID of the user.

        Returns:
            pd.DataFrame: List of agents assigned to user_id with model details.
        """
        query = f"""
            SELECT 
                A.AGENT_ID,
                A.AGENT_MODEL_ID,
                AM.AGENT_MODEL_NAME,
                AM.AGENT_MODEL_TYPE,
                AM.AGENT_MODEL_PROVIDER,
                A.AGENT_NAME,
                A.AGENT_DESCRIPTION,
                A.AGENT_TYPE,
                A.AGENT_MAX_OUT_TOKENS,
                A.AGENT_TEMPERATURE,
                A.AGENT_TOP_P,
                A.AGENT_TOP_K,
                A.AGENT_FREQUENCY_PENALTY,
                A.AGENT_PRESENCE_PENALTY,
                A.AGENT_PROMPT_SYSTEM,
                A.AGENT_PROMPT_MESSAGE,
                A.AGENT_DATE,
                A.AGENT_STATE,
                AU1.USER_ID,
                U1.USER_GROUP_ID,
                AU2.OWNER,
                AU2.USER_ID AS USER_ID_OWNER,                
                U2.USER_USERNAME,
                U2.USER_EMAIL,
                (
                    SELECT COUNT(1)
                    FROM AGENT_USER FU3
                    WHERE FU3.AGENT_ID = A.AGENT_ID
                    AND FU3.OWNER <> 1
                ) AS AGENT_USERS                              
            FROM 
                AGENTS A
            LEFT JOIN
                AGENT_MODELS AM 
                ON A.AGENT_MODEL_ID = AM.AGENT_MODEL_ID
            JOIN
                AGENT_USER AU1
                ON AU1.AGENT_ID = A.AGENT_ID
                AND AU1.USER_ID = {user_id}
            JOIN
                USERS U1
                ON U1.USER_ID = AU1.USER_ID
            JOIN 
                AGENT_USER AU2 
                ON AU2.AGENT_ID = A.AGENT_ID
                AND AU2.OWNER = 1
            JOIN
                USERS U2
                ON U2.USER_ID = AU2.USER_ID
            WHERE 
                A.AGENT_STATE <> 0
            ORDER BY 
                A.AGENT_ID DESC
        """
        return pd.read_sql(query, con=_self.conn)

    def copy_agent_to_admin(self, user_id):
        """
        Sincroniza los agentes compartidos por el admin (USER_ID = 0) con el usuario dado.
        Primero elimina los agentes no compartidos por el admin y luego inserta los nuevos.
        """
        query = """
        DECLARE
            agent_names VARCHAR2(4000) := '';
            separator   VARCHAR2(5) := '';
        BEGIN
            -- Primero eliminar agentes que ya no están compartidos por el admin
            DELETE FROM AGENT_USER AU_USER
            WHERE AU_USER.USER_ID = :user_id
            AND AU_USER.OWNER = 0
            AND NOT EXISTS (
                SELECT 1
                FROM AGENT_USER AU_ADMIN
                WHERE AU_ADMIN.AGENT_ID = AU_USER.AGENT_ID
                AND AU_ADMIN.USER_ID = 0
            );

            -- Luego insertar nuevos agentes compartidos por admin
            FOR base_agent IN (
                SELECT A.AGENT_ID, A.AGENT_NAME
                FROM AGENTS A
                JOIN AGENT_USER AU_ADMIN ON AU_ADMIN.AGENT_ID = A.AGENT_ID
                WHERE AU_ADMIN.USER_ID = 0
                AND A.AGENT_STATE <> 0
                AND NOT EXISTS (
                    SELECT 1
                    FROM AGENT_USER AU_USER
                    WHERE AU_USER.AGENT_ID = A.AGENT_ID
                    AND AU_USER.USER_ID = :user_id
                )
            ) LOOP
                INSERT INTO AGENT_USER (
                    agent_user_id,
                    agent_id,
                    user_id,
                    owner
                ) VALUES (
                    agent_user_id_seq.NEXTVAL,
                    base_agent.agent_id,
                    :user_id,
                    0
                );

                agent_names := agent_names || separator || base_agent.agent_name;
                separator := ', ';
            END LOOP;

            :agent_names := agent_names;
        END;
        """

        with self.conn.cursor() as cur:
            agent_name_var = cur.var(str)
            cur.execute(query, {"user_id": user_id, "agent_names": agent_name_var})
        self.conn.commit()

        return f"Agent(s): {agent_name_var.getvalue()} has been assigned successfully."


    def delete_agent_user_by_user(self, agent_id, user_id, agent_name):
        delete_query = """
            DELETE FROM AGENT_USER
            WHERE AGENT_ID = :agent_id AND USER_ID = :user_id
        """
        with self.conn.cursor() as cur:
            cur.execute(delete_query, {
                "agent_id": agent_id,
                "user_id": user_id
            })

        return f"You have been removed from access to agent **{agent_name}**."

    @st.cache_data
    def get_all_models(_self):
        """
        Retrieves all active agent models from the database.

        Returns:
            pd.DataFrame: A DataFrame containing agent model information.
        """
        query = """
            SELECT 
                AM.AGENT_MODEL_ID,
                AM.AGENT_MODEL_NAME,
                AM.AGENT_MODEL_TYPE,
                AM.AGENT_MODEL_PROVIDER,
                AM.AGENT_MODEL_SERVICE_ENDPOINT,
                AM.AGENT_MODEL_DATE
            FROM AGENT_MODELS AM
            WHERE 
                AM.AGENT_MODEL_STATE = 1
                AND AM.AGENT_MODEL_ID > 0
            ORDER BY 
                AM.AGENT_MODEL_ID ASC
        """
        return pd.read_sql(query, con=_self.conn)
    
    def insert_agent(
            self,
            agent_model_id,
            agent_name,
            agent_description,
            agent_type,
            agent_max_out_tokens,
            agent_temperature,
            agent_top_p,
            agent_top_k,
            agent_frequency_penalty,
            agent_presence_penalty,
            agent_prompt_system,
            agent_prompt_message,
            user_id
        ):
        """
        Inserts a new agent into the database. If agent name already exists, aborts.

        Args:
            agent_model_id (int): The ID of the agent model.
            agent_name (str): Name of the agent.
            agent_description (str): Description of the agent.
            agent_type (str): Type of agent.
            agent_max_out_tokens (int): Max output tokens.
            agent_temperature (float): Sampling temperature.
            agent_top_p (float): Top-p sampling.
            agent_top_k (int): Top-k sampling.
            agent_frequency_penalty (float): Frequency penalty.
            agent_presence_penalty (float): Presence penalty.
            agent_prompt_system (str): System prompt.
            agent_prompt_message (str): Message prompt.
            user_id (int): The user ID who owns this agent.

        Returns:
            str: A message indicating the result of the operation.
        """

        # Primero validar si ya existe un agente con el mismo nombre
        query = f"""
            SELECT 1 FROM AGENTS
            WHERE AGENT_NAME = '{agent_name}'
        """
        df = pd.read_sql(query, con=self.conn)

        if not df.empty:
            raise ValueError(f"Agent '{agent_name}' already exists. Please choose a different name.")

        # Insertamos el nuevo agente
        with self.conn.cursor() as cur:
            agent_id_var = cur.var(int)
            cur.execute(f"""
                INSERT INTO AGENTS (
                    AGENT_MODEL_ID,
                    AGENT_NAME,
                    AGENT_DESCRIPTION,
                    AGENT_TYPE,
                    AGENT_MAX_OUT_TOKENS,
                    AGENT_TEMPERATURE,
                    AGENT_TOP_P,
                    AGENT_TOP_K,
                    AGENT_FREQUENCY_PENALTY,
                    AGENT_PRESENCE_PENALTY,
                    AGENT_PROMPT_SYSTEM,
                    AGENT_PROMPT_MESSAGE
                ) VALUES (
                    {agent_model_id},
                    '{agent_name}',
                    '{agent_description}',
                    '{agent_type}',
                    {agent_max_out_tokens},
                    {agent_temperature},
                    {agent_top_p},
                    {agent_top_k},
                    {agent_frequency_penalty},
                    {agent_presence_penalty},
                    :agent_prompt_system,
                    :agent_prompt_message
                ) RETURNING AGENT_ID INTO :agent_id
            """, {
                "agent_prompt_system": agent_prompt_system,
                "agent_prompt_message": agent_prompt_message,
                "agent_id": agent_id_var
            })
        self.conn.commit()

        agent_id = agent_id_var.getvalue()[0]

        # Insertamos la relación AGENT_USER
        with self.conn.cursor() as cur:
            cur.execute(f"""
                INSERT INTO AGENT_USER (AGENT_ID, USER_ID)
                VALUES ({agent_id}, {user_id})
            """)
        self.conn.commit()

        return f"Agent '{agent_name}' has been created successfully.", agent_id

    def update_agent(
            self,
            agent_id,
            agent_name,
            agent_description,
            agent_max_out_tokens,
            agent_temperature,
            agent_top_p,
            agent_top_k,
            agent_frequency_penalty,
            agent_presence_penalty,
            state
        ):
        """
        Updates agent information in the database.

        Args:
            agent_id (int): The ID of the agent to update.
            agent_name (str): Updated agent name.
            agent_description (str): Updated agent description.
            agent_max_out_tokens (int): Updated max output tokens.
            agent_temperature (float): Updated temperature.
            agent_top_p (float): Updated top_p.
            agent_top_k (int): Updated top_k.
            agent_frequency_penalty (float): Updated frequency penalty.
            agent_presence_penalty (float): Updated presence penalty.
            state (int): Updated agent state.

        Returns:
            str: A message indicating success.
        """
        with self.conn.cursor() as cur:
            cur.execute(f"""
                UPDATE AGENTS SET 
                    AGENT_NAME              = :agent_name,
                    AGENT_DESCRIPTION       = :agent_description,
                    AGENT_MAX_OUT_TOKENS    = :agent_max_out_tokens,
                    AGENT_TEMPERATURE       = :agent_temperature,
                    AGENT_TOP_P             = :agent_top_p,
                    AGENT_TOP_K             = :agent_top_k,
                    AGENT_FREQUENCY_PENALTY = :agent_frequency_penalty,
                    AGENT_PRESENCE_PENALTY  = :agent_presence_penalty,
                    AGENT_STATE             = :state
                WHERE AGENT_ID = :agent_id
            """, {
                "agent_name": agent_name,
                "agent_description": agent_description,
                "agent_max_out_tokens": agent_max_out_tokens,
                "agent_temperature": agent_temperature,
                "agent_top_p": agent_top_p,
                "agent_top_k": agent_top_k,
                "agent_frequency_penalty": agent_frequency_penalty,
                "agent_presence_penalty": agent_presence_penalty,
                "state": state,
                "agent_id": agent_id
            })
        self.conn.commit()
        return f"Agent '{agent_name}' has been updated successfully."

    def update_agent_user(self, agent_id, user_ids):
        delete_query = "DELETE FROM AGENT_USER WHERE AGENT_ID = :agent_id AND OWNER = 0"
        with self.conn.cursor() as cur:
            cur.execute(delete_query, {"agent_id": agent_id})
            for uid in user_ids:
                cur.execute(
                    "INSERT INTO AGENT_USER (AGENT_USER_ID, AGENT_ID, USER_ID, OWNER) VALUES (AGENT_USER_ID_SEQ.NEXTVAL, :agent_id, :user_id, 0)",
                    {"agent_id": agent_id, "user_id": uid}
                )
        self.conn.commit()
        return f"Agent User relations for Agent ID [{agent_id}] updated successfully."
    
    def get_all_agent_user_cache(self, user_id, force_update=False):
        if force_update:
            self.get_all_agent_user.clear()
        return self.get_all_agent_user(user_id)

    @st.cache_data
    def get_all_agent_user(_self, user_id):
        """
        Retrieves AGENT_USER records for agents shared with other users (excluding current user_id).

        Args:
            user_id (int): The ID of the current user.

        Returns:
            pd.DataFrame: Shared AGENT_USER records (excluding agents belonging to user_id).
        """
        query = f"""
            SELECT 
                FU.AGENT_USER_ID,
                FU.AGENT_ID,
                F.AGENT_NAME,
                F.AGENT_DESCRIPTION,
                FU.USER_ID,
                U.USER_USERNAME,
                U.USER_NAME || ', ' || U.USER_LAST_NAME AS USER_FULL_NAME,
                UG.USER_GROUP_ID,
                UG.USER_GROUP_NAME,
                FU.OWNER,
                FU.AGENT_USER_STATE,
                FU.AGENT_USER_DATE
            FROM
                AGENT_USER FU
            JOIN AGENTS F 
                ON FU.AGENT_ID = F.AGENT_ID
            JOIN USERS U
                ON FU.USER_ID = U.USER_ID
            JOIN USER_GROUP UG
                ON U.USER_GROUP_ID = UG.USER_GROUP_ID
            WHERE
                FU.USER_ID <> {user_id}
                AND FU.OWNER <> 1
                AND F.AGENT_STATE <> 0
            ORDER BY
                FU.AGENT_USER_ID
        """
        return pd.read_sql(query, con=_self.conn)