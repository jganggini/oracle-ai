import click
import hashlib
import random
import string

from tool.autonomous_connection import connect_to_db
import os
import dotenv
from getpass import getpass

environment_variables = {
    "CON_CONDA_ENV_NAME": "ORACLE-AI",
    "CON_COMPARTMENT_ID": None,
    "CON_ADB_ADM_USER_NAME": "ADMIN",
    "CON_ADB_ADM_PASSWORD": "OracleAI123",
    "CON_ADB_ADM_SERVICE_NAME": "adw23ai_high",
    "CON_ADB_DEV_USER_NAME": "ADW23AI",
    "CON_ADB_DEV_PASSWORD": "OracleAI123",
    "CON_ADB_DEV_SERVICE_NAME": "adw23ai_medium",
    "CON_ADB_DEV_C_CREDENTIAL_NAME": "OCI_CRED",
    "CON_ADB_DEV_C_MODEL": "meta.llama-3.3-70b-instruct",
    "CON_ADB_WALLET_LOCATION": "../app/wallet",
    "CON_ADB_WALLET_PASSWORD": "OracleAI123",
    "CON_ADB_BUK_NAMESPACENAME": None,
    "CON_ADB_BUK_NAME": "ORACLE-AI-RAG",
    "CON_GEN_AI_SERVICE_ENDPOINT": "https://inference.generativeai.us-chicago-1.oci.oraclecloud.com",
    "CON_GEN_AI_EMB_MODEL_URL": "https://inference.generativeai.us-chicago-1.oci.oraclecloud.com/20231130/actions/embedText",
    "CON_GEN_AI_EMB_MODEL_ID": "cohere.embed-multilingual-v3.0",
    "CON_GEN_AI_CHAT_MODEL_ID": "meta.llama-3.3-70b-instruct",
    "CON_GEN_AI_AUTH_TYPE": "API_KEY",
}

MAX_TRIES = 3

@click.command()
def setup_environment():
    print("Setting up environment...")
    print("In order to run the application, please fill the values for the following elements")

    print("First, provide a compartment ID, this id should follow the format: ocid1.compartment.oc1..xxxxxx")
    input_compartment_id = input("Compartment ID: ")
    print(f"Compartment ID set to: {input_compartment_id}")
    environment_variables["CON_COMPARTMENT_ID"] = input_compartment_id

    random_string = ''.join(random.choices(string.ascii_letters, k=16))
    print(f"Random string generated: {random_string}")

    print("Now, set the database name")
    input_db_name = input("Database Name: ")
    environment_variables["CON_ADB_ADM_SERVICE_NAME"] = f"{input_db_name}_high"
    environment_variables["CON_ADB_DEV_SERVICE_NAME"] = f"{input_db_name}_medium"

    tries = 0
    while tries < MAX_TRIES:
        try:
            print("Now, set the password you have used when creating the database. Note that the password you have used when creating the wallet will be asked later.")
            input_admin_password = getpass("Password: ")

            print("Now, set the password you have used when creating the wallet.")
            input_wallet_password = getpass("Wallet Password: ")

            connect_to_db(
                user="ADMIN",
                password=input_admin_password,
                dsn=environment_variables["CON_ADB_ADM_SERVICE_NAME"],
                config_dir=environment_variables["CON_ADB_WALLET_LOCATION"],
                wallet_location=environment_variables["CON_ADB_WALLET_LOCATION"],
                wallet_password=input_wallet_password
            )
            print("Connection successful!")
            environment_variables["CON_ADB_ADM_PASSWORD"] = input_admin_password
            environment_variables["CON_ADB_DEV_PASSWORD"] = input_wallet_password
            environment_variables["CON_ADB_WALLET_PASSWORD"] = input_wallet_password
            break
        except Exception as e:
            tries += 1
            print(f"Connection failed: {e}. Attempt {tries} of {MAX_TRIES}. Maybe the password is incorrect?")
            if tries == MAX_TRIES:
                print("Maximum number of attempts reached. Exiting.")
                break

    print("Now, set the namespace name for the bucket where you will store the data.")
    input_namespace_name = input("Namespace Name: ")
    environment_variables["CON_ADB_BUK_NAMESPACENAME"] = input_namespace_name

    print("Environment setup complete.")

    # Save environment variables to .env file
    env_path = os.path.join("..", "app", ".env")
    with open(env_path, 'w') as env_file:
        for key, value in environment_variables.items():
            if value is not None:
                env_file.write(f"{key}={value}\n")
    print(f"Environment variables saved to {env_path}")


if __name__ == '__main__':
    setup_environment()