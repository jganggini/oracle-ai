import os
import sys
import oci
from dotenv import load_dotenv

# Cambiar al directorio `app/`
os.chdir(os.path.normpath(os.path.abspath(os.path.join(os.getcwd(), "..", "app"))))
print(f"[INFO] Directorio actual: {os.getcwd()}")

# Cargar variables de entorno desde .env en `app/`
env_path = os.path.join(os.getcwd(), ".env")
load_dotenv(dotenv_path=env_path)

# Se asume que la configuración OCI está correcta
config = oci.config.from_file(profile_name=os.getenv('CON_OCI_PROFILE_NAME', 'DEFAULT'))

# Obtener las variables de entorno requeridas
namespace_env  = os.getenv('CON_ADB_BUK_NAMESPACENAME')
bucket_name    = os.getenv('CON_ADB_BUK_NAME')

# Validar que todas las variables estén definidas
if not namespace_env:
    print("[ERROR] No se definió la variable de entorno 'CON_ADB_BUK_NAMESPACENAME'.")
    sys.exit(1)
if not bucket_name:
    print("[ERROR] No se definió la variable de entorno 'CON_ADB_BUK_NAME'.")
    sys.exit(1)

# Actualizar la región de la configuración si es necesario
bucket_region = config["region"]

# Crear el cliente de Object Storage
object_storage_client = oci.object_storage.ObjectStorageClient(config)

# Usar el namespace obtenido de la variable de entorno
namespace = namespace_env

# Validar que el bucket exista utilizando get_bucket
try:
    bucket = object_storage_client.get_bucket(namespace, bucket_name).data
    print(f"[OK] El bucket '{bucket_name}' existe en el namespace '{namespace_env}' y región '{bucket_region}'.")
except oci.exceptions.ServiceError as e:
    print(f"[ERROR] No se pudo encontrar el bucket '{bucket_name}' en el namespace '{namespace_env}':")
    sys.exit(e)