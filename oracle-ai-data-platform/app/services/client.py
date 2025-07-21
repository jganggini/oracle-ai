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
        os.chdir(os.path.normpath(os.path.abspath(os.path.join(os.getcwd(), "..", "app"))))
        
        if cls._instance is None:
            cls._instance = super(ClientService, cls).__new__(cls)
            cls._instance.config = oci.config.from_file(file_location=os.getenv("CON_ADB_OCI_CONFIG"))
            cls._instance.client = oci.object_storage.ObjectStorageClient(cls._instance.config)
        return cls._instance

    def get_client(self):
        return self.client

    def get_config(self):
        return self.config
