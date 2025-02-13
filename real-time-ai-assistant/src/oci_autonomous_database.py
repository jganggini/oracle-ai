import os
import oracledb
import pandas as pd

from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# Define connection parameters for Autonomous Database 23AI
connection_parameters = {
    "user_name"       : os.getenv('CON_DEV_USER_NAME'),
    "password"        : os.getenv('CON_DEV_PASSWORD'),
    "service_name"    : os.getenv('CON_DEV_SERVICE_NAME'),
    "wallet_location" : os.getenv('ZIP_WALLET_LOCATION'),
    "wallet_password" : os.getenv('CON_WALLET_PASSWORD')
}

def df_select_vw_contract_type(customer_code):
    """Fetch customer data from the database using a customer code"""
    # Use pandas to read the SQL query result into a DataFrame
    df = pd.DataFrame.ads.read_sql(
        f"SELECT ID AS CUSTOMER_ID, CUSTOMER_CODE, EMBED_DATA FROM VW_TELCO_CONTRACT_TYPE WHERE customer_code='{customer_code}'",
        connection_parameters=connection_parameters,
    )
    
    # Convert LOB data to text if necessary
    if 'EMBED_DATA' in df.columns:
        df['EMBED_DATA'] = df['EMBED_DATA'].apply(lambda x: x.read() if isinstance(x, oracledb.LOB) else x)
    
    return df

def df_insert_data(df, table_name):
    """Insert data from a Pandas DataFrame into a specified table in Oracle Autonomous Database"""
    # Convert all columns in the DataFrame to string type (if necessary)
    df = df.astype({
        col: 'str' for col in df.columns
    })
    
    # Convert date columns to datetime format if necessary
    date_columns = df.select_dtypes(include=['object']).columns[df.columns.str.contains('date|fecha')]
    for date_col in date_columns:
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        
    # Insert the DataFrame into the specified table
    df.ads.to_sql(
        table_name,
        connection_parameters=connection_parameters,
        if_exists="append"
    )

def df_select_calls(customer_code):
    """Fetch customer data from the database using a customer code"""
    # Use pandas to read the SQL query result into a DataFrame
    df = pd.DataFrame.ads.read_sql(f"""
         SELECT 
         CUSTOMER_CODE,
         CALL_HTML,
         CALL_SENTIMENTS_SENTENCE_METRIC,
         CALL_SENTIMENTS_SENTENCE_SCORE,
         TO_CHAR(call_date, 'YYYY-MM-DD HH24:MI:SS') AS CALL_DATE 
         FROM TELCO_CUSTOMER_CALLS 
         WHERE customer_code = '{customer_code}'
         """,
        connection_parameters=connection_parameters,
    )
    
    # Only keep columns of type object (typically strings)
    object_columns = df.select_dtypes(include=['object']).columns
    
    # Further filter columns that match 'date' or 'fecha'
    date_columns = object_columns[object_columns.str.contains('date|fecha', case=False, na=False)]
    
    # Convert matching columns to datetime
    for date_col in date_columns:
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    
    print(df)

    # Convert LOB (CLOB) data to text if necessary
    lob_columns = ['CALL_HTML']
    for column in lob_columns:
        if column in df.columns:
            df[column] = df[column].apply(lambda x: x.read() if isinstance(x, oracledb.LOB) else x)
    
    return df

# Creates the customers_vector table in the database.
def sp_elt_insert_into_docs(p_industry, p_case_name, p_view_name):
    
    # Autonomous Database 23AI    
    connection = oracledb.connect(
        user            = os.getenv('CON_DEV_USER_NAME'),
        password        = os.getenv('CON_DEV_PASSWORD'),
        dsn             = os.getenv('CON_DEV_SERVICE_NAME'),
        config_dir      = os.getenv('CON_WALLET_LOCATION'),
        wallet_location = os.getenv('CON_WALLET_LOCATION'),
        wallet_password = os.getenv('CON_WALLET_PASSWORD'),
    )

    # Connect to the database
    cursor = connection.cursor()

    try:
        cursor.execute(f"""
            CALL sp_elt_insert_into_docs('{p_industry}', '{p_case_name}', '{p_view_name}')
        """)
    
        # Commit si la operación modifica datos
        connection.commit()
    
    except oracledb.DatabaseError as e:
        error_obj, = e.args
        if error_obj.code == 955:  # ORA-00955: name is already used by an existing object
            print(f"Warning: {e}")
        else:
            print(f"Database error occurred: {e}")
            raise
    finally:
        # Close the connection
        cursor.close()
        connection.close()