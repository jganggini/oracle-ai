import os
import oci
from pathlib import Path

from dotenv import load_dotenv
import components as component
import services as service
import utils as utils

# Crear una instancia del servicio
client_service       = service.ClientService()
utl_function_service = utils.FunctionService()


load_dotenv()

class BucketService:
        
    @staticmethod
    def upload_file(object_name, put_object_body, msg: bool = False):
        """
        Uploads a file to the OCI Bucket.

        Args:
            object_name (str): Name of the object to upload.
            put_object_body  : Content of the file to be uploaded.

        Returns:
            Response object or error message.
        """
        try:
            name_from_path = utl_function_service.get_name_from_path(object_name)
            
            # Always create the .placeholder file in the folder
            folder_path = "/".join(object_name.split("/")[:-1]) + "/"
            client_service.get_client().put_object(
                namespace_name  = os.getenv('CON_ADB_BUK_NAMESPACENAME'),
                bucket_name     = os.getenv('CON_ADB_BUK_NAME'),
                object_name     = folder_path + ".placeholder",
                put_object_body = "" # Empty content
            )
            
            # Upload the file to the specified bucket
            response = client_service.get_client().put_object(
                namespace_name  = os.getenv('CON_ADB_BUK_NAMESPACENAME'),
                bucket_name     = os.getenv('CON_ADB_BUK_NAME'),
                object_name     = object_name,
                put_object_body = put_object_body
            )            

            # Check response status
            if response.status == 200:
                component.get_toast(f"The file '{name_from_path}' was uploaded to the Bucket successfully.", ":material/upload_file:") if msg else None
                return True
            else:
                component.get_error(f"[Error] Updating object:\n{response}")
                return False
        except Exception as e:
            component.get_error(f"[Error] Updating object:\n{e}")
            return False

    @staticmethod
    def delete_object(object_name, msg: bool = False):
        """
        Deletes a file from the OCI Bucket.

        Args:
            object_name (str): Name of the object to delete.

        Returns:
            Response object or error message.
        """
        try:
            name_from_path = utl_function_service.get_name_from_path(object_name)
            
            # Delete the file from the specified bucket
            response = client_service.get_client().delete_object(
                namespace_name = os.getenv('CON_ADB_BUK_NAMESPACENAME'),
                bucket_name    = os.getenv('CON_ADB_BUK_NAME'),
                object_name    = object_name
            )

            # Check response status
            if response.status == 204:
                component.get_toast(f"The '{name_from_path}' file was deleted successfully.", ":material/delete:") if msg else None
                return True
            else:
                component.get_error(f"[Error] Deleting Object:\n{response}")
                return True
        except Exception as e:
            component.get_error(f"[Error] Deleting Object:\n{e}")
            return False

    @staticmethod
    def get_object(object_name, msg: bool = False):
        """
        Retrieves an object from the OCI Bucket.

        Args:
            object_name (str): Name of the object to retrieve.

        Returns:
            Response object or a dictionary with error details.
        """
        try:
            name_from_path = utl_function_service.get_name_from_path(object_name)
            
            response = client_service.get_client().get_object(
                namespace_name = os.getenv('CON_ADB_BUK_NAMESPACENAME'),
                bucket_name    = os.getenv('CON_ADB_BUK_NAME'),
                object_name    = object_name
            )
            
            if response.status == 200:
                component.get_toast(f"Object '{name_from_path}' was successfully retrieved.", ":material/task:") if msg else None
                return response.data.content  # Return the content as bytes
            else:
                component.get_error(f"[Error] Retrieving Object:\n{response}")
                return None
        except Exception as e:
            component.get_error(f"[Error] Retrieving Object:\n{e}")
            return None
        
    @staticmethod
    def list_objects(folder_name, msg: bool = False):
        """
        Lists all objects in a given folder.

        Args:
            folder_name (str): The name of the folder (prefix).

        Returns:
            list: A list of object names in the folder.
        """
        try:
            response = client_service.get_client().list_objects(
                namespace_name = os.getenv('CON_ADB_BUK_NAMESPACENAME'),
                bucket_name    = os.getenv('CON_ADB_BUK_NAME'),
                prefix         = folder_name
            )
            component.get_toast(f"The listing successfully.", ":material/list:") if msg else None
            return [obj.name for obj in response.data.objects]
        except Exception as e:
            component.get_error(f"[Error] Listing Objects:\n{response}")
            return []
    
    def move_object(self, source_object_name, target_object_name, msg: bool = False):
        """
        Moves a file from one location to another in the OCI Bucket.

        Args:
            source_object_name (str): The name of the source object to move.
            target_object_name (str): The name of the target object where the file will be moved.

        Returns:
            dict: A summary of the move operation with status messages.
        """
        try:
            name_from_path = utl_function_service.get_name_from_path(source_object_name)
            
            # Step 1: Retrieve the source object
            object = self.get_object(source_object_name)
            
            # Step 2: Upload the file to the target location
            self.upload_file(target_object_name, object)

            # Step 3: Delete the source file
            self.delete_object(source_object_name)

            component.get_toast(f"The object '{name_from_path}' was moved successfully.", ":material/move_up:") if msg else None
            
        except Exception as e:
            component.get_error(f"[Error] Moving Object:\n {e}")
