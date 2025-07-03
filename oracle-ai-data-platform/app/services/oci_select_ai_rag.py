import os

from dotenv import load_dotenv
import components as component
import services.database as database

# Initialize the service
db_select_ai_rag_service = database.SelectAIRAGService()

load_dotenv()

class SelectAIRAGService:

    @staticmethod
    def get_profile(user_id: int) -> str:
        """
        Generates a profile name for the given user ID.

        Args:
            user_id (int): The ID of the user.

        Returns:
            str: The generated profile name.
        """        
        credential_name = os.getenv('CON_ADB_DEV_C_CREDENTIAL_NAME') 
        return (f"{credential_name}_RAG_{str(user_id)}").upper()
    
    @staticmethod
    def get_index_name(user_id: str) -> str:
        """
        Generates an index name for the given user ID.

        Args:
            user_id (str): The ID of the user.

        Returns:
            str: The generated index name.
        """
        profile_name = SelectAIRAGService.get_profile(user_id) 
        return f"IDX_{profile_name}"
    
    @staticmethod
    def create_profile(
            user_id,
            file_src_file_name
        ):
        """
        Creates a profile in the Select AI RAG system.

        Args:
            user_id (int): The ID of the user.
            file_src_file_name (str): The source file name associated with the profile.

        Returns:
            str: Success message if the profile is created.
        """
        try:
            profile_name = SelectAIRAGService.get_profile(user_id)
            index_name   = SelectAIRAGService.get_index_name(user_id)
            location     = f"{file_src_file_name.rsplit('/', 1)[0]}/"

            # Create Profile
            db_select_ai_rag_service.create_profile(
                profile_name,
                index_name,
                location
            )
            return f"[Select AI RAG] Module executed successfully."
        except Exception as e:
            component.get_error(f"[Error] Select AI RAG: {e}")