import oracledb
import os
import sys
from dotenv import load_dotenv

# Cambiar al directorio `app/`
os.chdir(os.path.normpath(os.path.abspath(os.path.join(os.getcwd(), "..", "app"))))
print(f"[INFO] Directorio actual: {os.getcwd()}")

# Cargar variables de entorno desde .env en `app/`
env_path = os.path.join(os.getcwd(), ".env")
load_dotenv(dotenv_path=env_path)

# Ruta del wallet dentro de `app/`
wallet_path = os.path.join(os.getcwd(), "wallet")

try:
    connection = oracledb.connect(
        user            = os.getenv('CON_ADB_ADM_USER_NAME'),
        password        = os.getenv('CON_ADB_ADM_PASSWORD'),
        dsn             = os.getenv('CON_ADB_ADM_SERVICE_NAME'),
        config_dir      = os.getenv('CON_ADB_WALLET_LOCATION'),
        wallet_location = wallet_path,
        wallet_password = os.getenv('CON_ADB_WALLET_PASSWORD')
    )

    print("[OK] Connection successful!")
    connection.close()

except Exception as e:
    sys.exit(e)
