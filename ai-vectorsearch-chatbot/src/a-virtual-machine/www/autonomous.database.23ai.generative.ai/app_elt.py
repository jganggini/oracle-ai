import os
import oracledb
import streamlit as st
import subprocess
import time
import pandas as pd
import ads

from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# Establish a connection to the Autonomous Database 23ai
connection = oracledb.connect(
    user            = os.getenv('CON_DEV_USER_NAME'),
    password        = os.getenv('CON_DEV_PASSWORD'),
    dsn             = os.getenv('CON_DEV_SERVICE_NAME'),
    config_dir      = os.getenv('CON_WALLET_LOCATION'),
    wallet_location = os.getenv('CON_WALLET_LOCATION'),
    wallet_password = os.getenv('CON_WALLET_PASSWORD')
)

# Define a dictionary with connection parameters for Autonomous Database 23ai
connection_parameters = {
    "user_name"       : os.getenv('CON_DEV_USER_NAME'),
    "password"        : os.getenv('CON_DEV_PASSWORD'),
    "service_name"    : os.getenv('CON_DEV_SERVICE_NAME'),
    "wallet_location" : os.getenv('ZIP_WALLET_LOCATION'),
    "wallet_password" : os.getenv('CON_WALLET_PASSWORD')
}

# Function to fetch and return customer data as a pandas DataFrame using ADS library
def df_customer():
    return pd.DataFrame.ads.read_sql(
        "SELECT * FROM telco_customers",
        connection_parameters=connection_parameters,
    )

# Function to handle adding a customer and executing related SQL scripts
def handle_add_customer(connection, num_customers):
    try:
        # Initialize a Streamlit message for displaying success or error messages
        success_message = st.empty()
        messages = "RUNNING..."
        success_message.success(messages)

        # Run a subprocess command to execute a Python script for adding customers
        subprocess.run(f"python config.case_telco.py {num_customers}", shell=True, check=True)
        messages += f"\n\nAdded {num_customers} record to tables: \
                      \n* TELCO_CUSTOMERS \
                      \n* TELCO_SUBSCRIPTION_PLAN \
                      \n* TELCO_CONTRACT_TYPE \
                      \n* TELCO_LAST_BILL_AMOUNT \
                      \n* TELCO_CUSTOMER_SATISFACTION \
                      \n\nExecute proceduces for cases:"
        success_message.success(messages)

        # List of SQL files to be executed after adding customers
        sql_files = [
            "./plsql/developer/2.case_telco/g.SP_ETL_INSERT_INTO_TELCO_CONTRACT_TYPE.sql",
            "./plsql/developer/2.case_telco/h.SP_ETL_INSERT_INTO_TELCO_CUSTOMER_SATISFACTION.sql",
            "./plsql/developer/2.case_telco/i.SP_ETL_INSERT_INTO_TELCO_LAST_BILL_AMOUNT.sql",
            "./plsql/developer/2.case_telco/j.SP_ETL_INSERT_INTO_TELCO_SUSCRIPTION_PLAN.sql"
        ]
        
        # Execute each SQL file within a database cursor context
        with connection.cursor() as cursor:
            for sql_file in sql_files:
                with open(sql_file, 'r') as file:
                    cursor.execute(file.read())
                    # Update success message with each executed SQL file
                    messages += f"\n* {'_'.join(os.path.splitext(os.path.basename(sql_file))[0].split('_')[4:])}"
                    success_message.success(messages)
        
        # Pause for a short duration to allow messages to display, then clear the success message
        time.sleep(5)
        success_message.empty()

    except (subprocess.CalledProcessError, ValueError) as e:
        st.error(f"Error al ejecutar el script: {e}")

# Main function to set up the chatbot interface and ETL operations
def app_elt():
    # Retrieve the number of customers to add from environment variables
    num_customers = os.getenv('NUM_CUSTOMERS')
    
    # Set the header for the Streamlit application
    st.header("_Vector Search in_ :red[ADW 23AI] :sunglasses:")

    # Set the caption/subtitle for additional description
    st.caption("Vector Search + :gray[Generative AI]")

    # Configure the sidebar in the Streamlit application
    with st.sidebar:
        
        # Display an animated image or logo in the sidebar
        st.image('https://raw.githubusercontent.com/jganggini/oracle-ai/main/autonomous-database-23ai-vectorsearch-chatbot/src/img/chatbot_ai.gif')
        
        # Add an expander section to show additional information about the project
        with st.expander("See Explanation"):
            st.write('''
                Este proyecto de chatbot utiliza Autonomous Database 23AI 
                para explorar y consultar datos dentro de las tablas. 
                Se han incorporado industrias y casos que agrupan 
                las tablas utilizando embeddings, lo que facilita 
                la extracción de información relevante. Además, 
                se ha implementado Generative AI para mejorar 
                la precisión y eficiencia en la búsqueda y consulta 
                de casos específicos dentro del chatbot.
            ''')

        # Add a button to trigger the customer addition function
        if st.button("🫡 Add Customer"):
            handle_add_customer(connection, num_customers)

        # Display a footer message with a link to the author's LinkedIn profile
        st.html('''
            <p style="font-size: 12px; text-align: center;">
                Made with ❤️ in Oracle AI · Powered by <a href="https://pe.linkedin.com/in/jganggini" target="_blank">Joel Ganggini</a>
            </p>
        ''')

    # Display the customers table in the main content area
    st.write("Customers Table")
    df = df_customer()
    st.dataframe(df, height=700)
