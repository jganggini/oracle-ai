import os
import time

from dotenv import load_dotenv
import components as component
import services.database as database

# Initialize the service
db_select_ai_service = database.SelectAIService()

load_dotenv()

class SelectAIService:

    @staticmethod
    def get_profile(user_id: int) -> str:
        """
        Generates a profile name for the given user ID.

        Args:
            user_id (int): The ID of the user.

        Returns:
            str: The generated profile name.
        """
        credential_name = os.getenv('CON_ADB_DEV_USER_NAME') if user_id == 0 else (f"{os.getenv('CON_ADB_DEV_C_CREDENTIAL_NAME')}_SEL_{str(user_id)}").upper()
        
        return credential_name
    
    @staticmethod
    def create_profile(user_id):   
        """
        Creates a profile for Select AI.

        Args:
            user_id (int): The ID of the user.
        """
        try:
            profile_name = SelectAIService.get_profile(user_id)
        
            # Create Profile
            db_select_ai_service.create_profile(
                    profile_name,
                    user_id
            )
            component.get_success("[Select AI] Profile was created successfully.", ":material/person_add:")
        except Exception as e:
            component.get_error(f"[Error] Select AI - Create Profile:\n{e}")
        
    @staticmethod
    def create(
            user_id,
            file_src_file_name, 
            file_trg_obj_name,
            comment_data_editor
        ):
        """
        Creates a table from a CSV file and updates it with comments, then creates a profile.

        Args:
            user_id (int): The ID of the user.
            file_src_file_name (str): The source file name.
            file_trg_obj_name (str): The target table name.
            comment_data_editor (pd.DataFrame): DataFrame containing comments to update.

        Returns:
            str: A success message if the operation is completed successfully.
        """
        try:
            profile_name = SelectAIService.get_profile(user_id)
            object_uri   = file_src_file_name
            table_name   = file_trg_obj_name
            
            # Create table
            db_select_ai_service.create_table_from_csv(
                object_uri,
                table_name
            ) 
            component.get_toast(f"Table '{table_name}' has been created successfully.", ":material/database:")

            comments_added = 0
            if comment_data_editor is not None and not comment_data_editor.empty:
                for _, row in comment_data_editor.iterrows():
                    # Only update if the comment is not empty
                    if row["Comment"].strip():
                        db_select_ai_service.update_comment(
                            table_name  = file_trg_obj_name,
                            column_name = row["Column Name"],
                            comment     = row["Comment"]
                        )
                        comments_added += 1
                
                # Show a message if at least one comment was added
                if comments_added > 0:
                    component.get_toast(f"Comment(s) have been added successfully.", ":material/notes:")
            
            # Create Profile
            db_select_ai_service.create_profile(
                profile_name,
                user_id
            )

            db_select_ai_service.get_tables_cache(user_id, force_update=True)

            return f"[Select AI]: Module executed successfully."
        except Exception as e:
            component.get_error(f"[Error] Select AI: {e}")