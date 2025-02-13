import os
import sys
import ads
import pandas as pd
from faker import Faker
from dotenv import load_dotenv
import random

# Cargar las variables de entorno desde el archivo .env
load_dotenv()

# 
user_developer    = os.getenv('CON_DEV_USER_NAME')
print(f"Usuario de desarrollo cargado: {user_developer}")

# Inicializar Faker
fake = Faker()

def generate_telco_customers(num_customers):
    data = {
        'customer_id': [fake.unique.random_int(min=1000, max=99999) for _ in range(num_customers)],
        'customer_code': [f"{i:03d}-{j:04d}" for i, j in zip([0]*num_customers, range(1, num_customers + 1))],  # Formato 000-0001
        'first_name': [fake.first_name() for _ in range(num_customers)],
        'last_name': [fake.last_name() for _ in range(num_customers)],
        'email': [fake.email() for _ in range(num_customers)],
        'phone_number': [fake.phone_number() for _ in range(num_customers)],
        'address': [fake.address() for _ in range(num_customers)],
        'city': [fake.city() for _ in range(num_customers)],
        'state': [fake.state() for _ in range(num_customers)],
        'postal_code': [fake.postcode() for _ in range(num_customers)],
        'country': [fake.country() for _ in range(num_customers)]
    }
    df = pd.DataFrame(data)
    insert_data_to_adb(df, "telco_customers")
    print(f"      > {user_developer}.TELCO_CUSTOMERS")
    return df

def generate_telco_contract_type(customer_ids):
    data = {
        'contract_id': [fake.unique.random_int(min=1000, max=99999) for _ in range(len(customer_ids))],
        'customer_id': customer_ids,
        'contract_type': [random.choice(['Prepaid', 'Postpaid', 'No Contract']) for _ in range(len(customer_ids))]
    }
    insert_data_to_adb(pd.DataFrame(data), "telco_contract_type")
    print(f"      > {user_developer}.TELCO_CONTRACT_TYPE")

def insert_data_to_adb(df, table_name):
    # Autonomous Database 23AI
    connection_parameters = {
        "user_name"       : os.getenv('CON_DEV_USER_NAME'),
        "password"        : os.getenv('CON_DEV_PASSWORD'),
        "service_name"    : os.getenv('CON_DEV_SERVICE_NAME'),
        "wallet_location" : os.getenv('ZIP_WALLET_LOCATION'),
        "wallet_password" : os.getenv('CON_WALLET_PASSWORD')
    }
    
    # Ajustar los tipos de datos en el DataFrame según sea necesario
    df = df.astype({
        col: 'str' for col in df.columns
    })
    
    # Convert date columns to datetime format if necessary
    date_columns = df.select_dtypes(include=['object']).columns[df.columns.str.contains('date|fecha')]
    for date_col in date_columns:
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')

    # Insertar el DataFrame en la tabla especificada
    df.ads.to_sql(
        table_name,
        connection_parameters=connection_parameters,
        if_exists="append"
    )

if __name__ == "__main__":
    
    print(f"[OK] INSERT INTO THE CASE TABLES........................................[INSERT_DATA]")

    num_customers = int(sys.argv[1])

    customers_df = generate_telco_customers(num_customers=num_customers)
    generate_telco_contract_type(customer_ids=customers_df['customer_id'])