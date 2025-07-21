import os
import sys

import oracledb
from dotenv import load_dotenv


def connect_to_db(user, password, dsn, config_dir, wallet_location, wallet_password):
    """
    Connect to the Oracle database using the provided credentials and wallet.
    """
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
            user            = user,
            password        = password,
            dsn             = dsn,
            config_dir      = config_dir,
            wallet_location = wallet_path,
            wallet_password = wallet_password
        )

        print("[OK] Connection successful!")
        connection.close()

    except Exception as e:
        sys.exit(e)


if __name__ == "__main__":
    # Cargar las variables de entorno desde el archivo .env
    load_dotenv("../app/.env")
    # Obtener las variables de entorno necesarias
    user = os.getenv('CON_ADB_ADM_USER_NAME')
    password = os.getenv('CON_ADB_ADM_PASSWORD')
    dsn = os.getenv('CON_ADB_ADM_SERVICE_NAME') 
    config_dir = os.getenv('CON_ADB_WALLET_LOCATION')
    wallet_location = os.getenv('CON_ADB_WALLET_LOCATION')
    wallet_password = os.getenv('CON_ADB_WALLET_PASSWORD')

    # Conectar a la base de datos
    connect_to_db(user, password, dsn, config_dir, wallet_location, wallet_password)
    print("[INFO] Finished connecting to the database.")
