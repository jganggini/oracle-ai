import os
import subprocess
import sys
import oracledb
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# 
env_name          = os.getenv('CONDA_ENV_NAME')
requirements_file = os.getenv('CONDA_REQUIREMENTS_FILE')
user_admin        = os.getenv('CON_ADMIN_USER_NAME')
user_developer    = os.getenv('CON_DEV_USER_NAME')
num_customers     = os.getenv('NUM_CUSTOMERS')

# 
def check_conda():
    try:
        subprocess.run("conda --version", shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError:
        print("Error: Conda no está instalado en tu sistema.")
        print("Por favor, instala Conda antes de continuar. Puedes descargarlo desde: https://docs.conda.io/projects/conda/en/latest/user-guide/install/")
        sys.exit(1)

# Creates the customers_vector table in the database.
def adw23ai_execute(user, plsq):
    
    # Read the SQL script from the file
    with open(plsq, 'r') as file:
        plsq = file.read()

    # Autonomous Database 23AI    
    connection = oracledb.connect(
        user            = user_admin if user == "ADMIN" else user_developer,
        password        = os.getenv('CON_ADMIN_PASSWORD') if user == "ADMIN" else os.getenv('CON_DEV_PASSWORD'),
        dsn             = os.getenv('CON_ADMIN_SERVICE_NAME') if user == "ADMIN" else os.getenv('CON_DEV_SERVICE_NAME'),
        config_dir      = os.getenv('CON_WALLET_LOCATION'),
        wallet_location = os.getenv('CON_WALLET_LOCATION'),
        wallet_password = os.getenv('CON_WALLET_PASSWORD'),
    )

    # Connect to the database
    cursor = connection.cursor()

    try:
        cursor.execute(plsq)
    
    except oracledb.DatabaseError as e:
        error_obj, = e.args
        if error_obj.code == 955:  # ORA-00955: name is already used by an existing object
           print(e)
        else:
            raise
    finally:
        # Close the connection
        cursor.close()
        connection.close()

def main():
    print(f"\n                                                                [Config: Environment]")
    print(f"-------------------------------------------------------------------------------------")

    check_conda()
    print(f"[OK] CHECK CONDA........................................................[CHECK_CONDA]")
      
    subprocess.run(f"conda create -n {env_name} python=3.9 -y", shell=True, check=True, stdout=subprocess.DEVNULL)
    print(f"[OK] CONDA CREATE ENVIRONMENT.....................................[CONDA_ENVIRONMENT]")

    conda = f"conda activate {env_name}"  
    subprocess.run(conda, shell=True, check=True, stdout=subprocess.DEVNULL)
    print(f"[OK] CONDA ACTIVATE...............................................[CONDA_ENVIRONMENT]")

    subprocess.run(f"{conda} && pip install --force-reinstall -r {requirements_file}", shell=True, check=True, stdout=subprocess.DEVNULL)
    print(f"[OK] PIP INSTALL REQUIREMENTS.....................................[CONDA_ENVIRONMENT]")

    print(f"\n                                                   [PL/SQL: Autonomous Database 23ai]")
    print(f"-------------------------------------------------------------------------------------")
    
    print(f"[USER: {user_admin}]")
    
    adw23ai_execute(user_admin, "./plsql/admin/1.CREATE_USER.sql")
    print("[OK] CREATE USER DEVELOPER..............................................[CREATE_USER]")

    adw23ai_execute(user_admin, "./plsql/admin/2.GRANT_DWROLE.sql")
    print("[OK] GRANT DWROLE TO DEVELOPER.........................................[GRANT_DWROLE]")
    
    adw23ai_execute(user_admin, "./plsql/admin/3.GRAN_EXECUTE_DBMS_VECTOR.sql")
    print("[OK] GRANT EXECUTE ON DBMS_VECTOR TO DEVELOPER.............[GRAN_EXECUTE_DBMS_VECTOR]")
    
    adw23ai_execute(user_admin, "./plsql/admin/4.GRAN_EXECUTE_DBMS_VECTOR_CHAIN.sql")
    print("[OK] GRANT EXECUTE ON DBMS_VECTOR_CHAIN TO DEVELOPER.[GRAN_EXECUTE_DBMS_VECTOR_CHAIN]")
    
    adw23ai_execute(user_admin, "./plsql/admin/5.DBMS_NETWORK_ACL_ADMIN.sql")
    print("[OK] DBMS_NETWORK_ACL_ADMIN.APPEND_HOST_ACE..................[DBMS_NETWORK_ACL_ADMIN]")
    
    print(f"\n[USER: {user_developer}]")

    adw23ai_execute(user_developer, "./plsql/developer/1.user/a.CREATE_CREDENTIAL.sql")
    print("[OK] DBMS_VECTOR.CREATE_CREDENTIAL................................[CREATE_CREDENTIAL]")

    adw23ai_execute(user_developer, "./plsql/developer/1.user/b.CREATE_TABLE_ACCESS_CASES.sql")
    print("[OK] CREATE TABLE ACCESS FOR CASES.....................................[CREATE_TABLE]")

    adw23ai_execute(user_developer, "./plsql/developer/1.user/c.CREATE_TABLE_DOCS.sql")
    print("[OK] CREATE DOCS TABLE FOR ALL CASES...........................[VECTOR][CREATE_TABLE]")
    print(f"      > {user_developer}.DOCS")

    adw23ai_execute(user_developer, "./plsql/developer/1.user/d.CREATE_SP_ELT_INSERT_INTO_DOCS.sql")
    print("[OK] CREATE PROCEDURE FOR ALL CASES........................[VECTOR][CREATE_PROCEDURE]")
    print(f"      > {user_developer}.SP_ETL_INSERT_INTO_DOCS(p_industry, p_case_name, p_view_name)")

    print(f"\n[USER: {user_developer}][CASE: TELCO]")
    
    adw23ai_execute(user_developer, "./plsql/developer/2.case_telco/a.CREATE_TABLES.sql")
    print("[OK] CREATE TABLE DOCS FOR VECTORS....................................[CREATE_TABLES]")
    print(f"      > {user_developer}.TELCO_CUSTOMERS")
    print(f"      > {user_developer}.TELCO_SUBSCRIPTION_PLAN")
    print(f"      > {user_developer}.TELCO_CONTRACT_TYPE")
    print(f"      > {user_developer}.TELCO_LAST_BILL_AMOUNT")
    print(f"      > {user_developer}.TELCO_CUSTOMER_SATISFACTION")

    subprocess.run(f"{conda} && python config.case_telco.py {num_customers}", shell=True, check=True)

    print(f"[OK] CREATE VIEWS FOR CASES.............................................[CREATE_VIEW]")

    adw23ai_execute(user_developer, "./plsql/developer/2.case_telco/b.CREATE_VW_TELCO_CONTRACT_TYPE.sql")
    print(f"      > {user_developer}.VW_TELCO_CONTRACT_TYPE")

    adw23ai_execute(user_developer, "./plsql/developer/2.case_telco/c.CREATE_VW_TELCO_CUSTOMER_SATISFACTION.sql")
    print(f"      > {user_developer}.VW_TELCO_CUSTOMER_SATISFACTION")
    
    adw23ai_execute(user_developer, "./plsql/developer/2.case_telco/d.CREATE_VW_TELCO_LAST_BILL_AMOUNT.sql")
    print(f"      > {user_developer}.VW_TELCO_LAST_BILL_AMOUNT")
    
    adw23ai_execute(user_developer, "./plsql/developer/2.case_telco/e.CREATE_VW_TELCO_SUSCRIPTION_PLAN.sql")
    print(f"      > {user_developer}.VW_TELCO_SUSCRIPTION_PLAN")
    
    adw23ai_execute(user_developer, "./plsql/developer/2.case_telco/f.INSERT_INTO_ACCCESS_CASES.sql")
    print("[OK] CREATE TABLE ACCESS FOR CASES.....................................[CREATE_TABLE]")

    print("[OK] EXECUTE SP SP_ETL_INSERT_INTO_DOCS................................[ELT][EXECUTE]")

    adw23ai_execute(user_developer, "./plsql/developer/2.case_telco/g.SP_ETL_INSERT_INTO_TELCO_CONTRACT_TYPE.sql")
    print(f"      > {user_developer}.SP_ETL_INSERT_INTO_DOCS('TELCO', 'Contract Type', 'vw_telco_contra...")

    adw23ai_execute(user_developer, "./plsql/developer/2.case_telco/h.SP_ETL_INSERT_INTO_TELCO_CUSTOMER_SATISFACTION.sql")
    print(f"      > {user_developer}.SP_ETL_INSERT_INTO_DOCS('TELCO', 'Customer Satisfaction', 'vw_telc...")

    adw23ai_execute(user_developer, "./plsql/developer/2.case_telco/i.SP_ETL_INSERT_INTO_TELCO_LAST_BILL_AMOUNT.sql")
    print(f"      > {user_developer}.SP_ETL_INSERT_INTO_DOCS('TELCO', 'Last Bill Amount', 'vw_telco_las...")

    adw23ai_execute(user_developer, "./plsql/developer/2.case_telco/j.SP_ETL_INSERT_INTO_TELCO_SUSCRIPTION_PLAN.sql")
    print(f"      > {user_developer}.SP_ETL_INSERT_INTO_DOCS('TELCO', 'Subscription Plan', 'vw_telco_su...")

    adw23ai_execute(user_developer, "./plsql/developer/3.CREATE_INDEX_DOCS.sql")
    print("[OK] CREATE INDEX DOCS_HNSW_IDX...................................[CREATE_INDEX_DOCS]")

    subprocess.run(f"{conda} && streamlit run app.py --server.port 8502", shell=True, check=True)

if __name__ == "__main__":
    main()

# PLSQL> drop user adw23ai cascade;
# CMD> conda deactivate
# CMD> conda remove --name adw23ai --all -y
