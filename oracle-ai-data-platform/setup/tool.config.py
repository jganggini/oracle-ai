import oci
import os
import sys

try:
    # Default: C:\Users\jeggg\.oci\config
    # # Cargar la configuración desde el archivo por defecto (por lo general: ~/.oci/config)
    config = oci.config.from_file(profile_name=os.getenv('CON_OCI_PROFILE_NAME', 'DEFAULT'))

    # Variables requeridas en el archivo de configuración
    required_keys = ['user', 'fingerprint', 'tenancy', 'region', 'key_file']

    missing = [key for key in required_keys if not config.get(key)]
    if missing:
        raise ValueError(f"Las siguientes variables faltan en el archivo de configuración: {', '.join(missing)}")

    # Asignación de variables
    user_ocid     = config['user']
    fingerprint   = config['fingerprint']
    tenancy_ocid  = config['tenancy']
    region        = config['region']
    key_file_path = config['key_file']

    print("[OK] Archivo de configuración cargado correctamente!")
    print(f"[INFO] User OCID      : {user_ocid}")
    print(f"[INFO] Fingerprint    : {fingerprint}")
    print(f"[INFO] Tenancy OCID   : {tenancy_ocid}")
    print(f"[INFO] Region         : {region}")
    print(f"[INFO] Key File Path  : {key_file_path}")

    # Validar que la clave privada exista y se pueda leer
    if not os.path.isfile(key_file_path):
        raise FileNotFoundError(f"No se encontró el archivo de clave privada en: {key_file_path}")
        
    with open(key_file_path, 'r') as key_file:
        private_key = key_file.read().strip()
        if not private_key:
            raise ValueError("El archivo de clave privada está vacío.")

    print("[OK] Clave privada cargada correctamente!")

except Exception as e:
    print("[ERROR] Falló la validación del archivo de configuración OCI:")
    sys.exit(e)