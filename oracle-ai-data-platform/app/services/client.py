import oci
import os

from dotenv import load_dotenv

load_dotenv()

class ClientService:
    """
    Singleton class for establishing a connection to OCI Object Storage and providing the client.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ClientService, cls).__new__(cls)
            cls._instance.config = oci.config.from_file(profile_name=os.getenv('CON_OCI_PROFILE_NAME', 'DEFAULT'))
            cls._instance.client = oci.object_storage.ObjectStorageClient(cls._instance.config)
        return cls._instance

    def get_client(self):
        return self.client

    def get_config(self):
        return self.config
