import os
import ads
import oracledb
from dotenv import load_dotenv

load_dotenv()

class Connection:
    """
    Singleton class for managing a reusable Oracle database connection.

    Ensures only one instance of the connection is created and reused throughout the application.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Connection, cls).__new__(cls)
            cls._instance.conn = oracledb.connect(
                user            = os.getenv('CON_ADB_DEV_USER_NAME'),
                password        = os.getenv('CON_ADB_DEV_PASSWORD'),
                dsn             = os.getenv('CON_ADB_DEV_SERVICE_NAME'),
                config_dir      = os.getenv('CON_ADB_WALLET_LOCATION'),
                wallet_location = os.getenv('CON_ADB_WALLET_LOCATION'),
                wallet_password = os.getenv('CON_ADB_WALLET_PASSWORD')
            )
            cls._instance.conn.autocommit = True  # Always enable autocommit
        return cls._instance

    def get_connection(self):
        """
        Returns the Oracle database connection instance.

        Returns:
            oracledb.Connection: The database connection object.
        """
        return self.conn

    def close_connection(self):
        """
        Closes the Oracle database connection if it is open.
        """
        if self.conn is not None:
            try:
                self.conn.close()
                self.conn = None
            except oracledb.DatabaseError as e:
                error, = e.args
                print(f"Error closing the database connection: {error.message}")
                raise

    def __enter__(self):
        """
        Enables the use of the class in a context manager (with statement).

        Returns:
            Connection: The current instance of the connection class.
        """
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Ensures the connection is closed when exiting the context.
        """
        self.close_connection()