
import pandas as pd
from services.database.connection import Connection

class SelectAIRAGService:
    """
    Service class for handling Select AI RAG (Retrieve and Generate) operations.
    """

    def __init__(self):
        """
        Initializes the SelectAIRAGService with a shared database connection.
        """
        self.conn_instance = Connection()
        self.conn = self.conn_instance.get_connection()

    def create_profile(
            self,
            profile_name,
            index_name,
            location
        ):
        """
        Creates a new profile in the database for Select AI RAG.

        Args:
            profile_name (str) : The name of the profile to create.
            index_name (str)   : The name of the index associated with the profile.
            location (str)     : The location for the profile.
        """
        with self.conn.cursor() as cur:
            cur.execute(f"""
                BEGIN
                    SP_SEL_AI_RAG_PROFILE('{profile_name}', '{index_name}', '{location}');
                END;
            """)
        self.conn.commit()
    
    def get_chat(
            self,
            prompt,
            profile_name,
            action,
            language
        ):
        """
        Generates a chat response using the Select AI RAG profile.

        Args:
            prompt (str)       : The user prompt or query.
            profile_name (str) : The name of the profile to use.
            action (str)       : The action to perform.
            language (str)     : The language for the response.

        Returns:
            str: The generated chat response.
        """
        query = f"""
            SELECT
                DBMS_CLOUD_AI.GENERATE(
                prompt       => '{prompt} /** Format the response in markdown. Do not underline titles. Just focus on the information in the documents. Answer in {language}. If you do not know the answer, answer imperatively and exactly: ''NNN.'' **/',
                profile_name => '{profile_name}',
                action       => '{action}') AS CHAT
            FROM DUAL
        """
        return pd.read_sql(query, con=self.conn)["CHAT"].iloc[0].read()
    
    def get_files( self, index_name):
        """
        Retrieves file details and content from the specified index.

        Args:
            index_name (str): The name of the index to query.

        Returns:
            pd.DataFrame or None: A DataFrame containing file details and content, or None if the index does not exist.
        """
        try:
            query = f"""
                SELECT 
                    JSON_VALUE(ATTRIBUTES, '$.object_name')   AS FILE_NAME,
                    JSON_VALUE(ATTRIBUTES, '$.object_size')   AS OBJECT_SIZE,
                    JSON_VALUE(ATTRIBUTES, '$.last_modified') AS LAST_MODIFIED,
                    JSON_VALUE(ATTRIBUTES, '$.location_uri')  AS LOCATION_URI,
                    JSON_VALUE(ATTRIBUTES, '$.start_offset')  AS START_OFFSET,
                    JSON_VALUE(ATTRIBUTES, '$.end_offset')    AS END_OFFSET,
                    DBMS_LOB.SUBSTR(CONTENT, 4000, 1)         AS CONTENT
                FROM 
                    {index_name}$VECTAB
            """
            return pd.read_sql(query, con=self.conn)
        except Exception as e:
            # Table or view '{index_name}$VECTAB' does not exist.
            if 'ORA-00942' in str(e):
                return None