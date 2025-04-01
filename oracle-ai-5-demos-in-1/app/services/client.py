import oci
from dotenv import load_dotenv
import os

load_dotenv()

class ClientService:
    """
    Singleton class for establishing a connection to OCI Object Storage and providing the client.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ClientService, cls).__new__(cls)
            cls._instance.client = oci.object_storage.ObjectStorageClient(
                oci.config.from_file(profile_name=os.getenv('CON_PROFILE_NAME')) # Load the config from ~/.oci/config
            )
        return cls._instance

    def get_client(self):
         """
        Returns the OCI Object Storage client instance.

        Returns:
            oci.object_storage.ObjectStorageClient: The Object Storage client instance.
        """
         return self.client