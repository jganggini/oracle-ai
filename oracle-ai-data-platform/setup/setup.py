"""
    ---------------------------------------------
    Prerequisites
    ---------------------------------------------
    1. Autonomous Database 23ai
    2. OCI Bucket
    ---------------------------------------------
"""
import os
import sys
import subprocess
import shutil

# Ruta absoluta o relativa al archivo .env
file_path = os.path.dirname(__file__)
base_path = os.path.dirname(file_path)
app_path  = os.path.join(base_path, 'app')
env_path  = os.path.join(app_path, '.env')
wall_path = os.path.join(app_path, 'wallet')

# Verificar si el archivo .env existe
if not os.path.exists(env_path):
    print(f'El archivo .env no existe en: {env_path}')
    sys.exit(1)

# Verificar si la carpeta wallet existe
if not os.path.exists(wall_path):
    print(f'El archivo wallet no existe en: {wall_path}')
    sys.exit(1)

def get_private_key(key_file_path):
    # Leer y procesar la clave privada
    with open(key_file_path, 'r') as key_file:
        private_key_lines = key_file.readlines()
    
    # Eliminar líneas específicas (BEGIN y END)
    private_key_lines = [
        line.strip() for line in private_key_lines 
        if line.strip() not in ('-----BEGIN PRIVATE KEY-----', '-----END PRIVATE KEY-----')
        if line.strip() not in ('-----BEGIN RSA PRIVATE KEY-----', '-----END RSA PRIVATE KEY-----')
    ]
    
    # Combinar las líneas restantes en una sola cadena
    private_key = ''.join(private_key_lines)
    
    # Reemplazar saltos de línea y escapar comillas simples
    private_key = private_key.replace('\n', '').replace("'", "''")
    
    return private_key

# 
def conda(command, message):
    try:
        if 'CHECK_CONDA' in message:
            subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print(message)
        else:
            subprocess.run(command, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            print(message)
    except subprocess.CalledProcessError as e:
        error_output = e.stderr.decode('utf-8') if e.stderr else str(e)
        if 'EnvironmentLocationNotFound' in error_output:
            print(message.replace('OK', '--'))
            print("[Warning]:\n" + error_output.rstrip('\n'))
        else:
            print(f'[Error]: {error_output}')
            print(f'[Command]: {command}')
            sys.exit(1)

#
def exec(user, file_name, message):
    import oci
    import oracledb
    from dotenv import load_dotenv

    load_dotenv(dotenv_path=env_path)
    
    # Default: C:\Users\jeggg\.oci\config
    config = oci.config.from_file(profile_name=os.getenv('CON_OCI_PROFILE_NAME', 'DEFAULT'))

    # ADW23ai: Admin
    con_adb_adm_user_name       = os.getenv('CON_ADB_ADM_USER_NAME')
    con_adb_adm_password        = os.getenv('CON_ADB_ADM_PASSWORD')
    con_adb_adm_service_name    = os.getenv('CON_ADB_ADM_SERVICE_NAME')

    # ADW23ai: Developer
    con_adb_dev_user_name         = os.getenv('CON_ADB_DEV_USER_NAME')
    con_adb_dev_password          = os.getenv('CON_ADB_DEV_PASSWORD')
    con_adb_dev_service_name      = os.getenv('CON_ADB_DEV_SERVICE_NAME')
    con_adb_dev_comparment_ocid   = os.getenv('CON_COMPARTMENT_ID')
    con_adb_dev_c_user_ocid       = config['user']
    con_adb_dev_c_tenancy_ocid    = config['tenancy']
    con_adb_dev_c_private_key     = get_private_key(config['key_file'])
    con_adb_dev_c_fingerprint     = config['fingerprint']
    con_adb_dev_c_credential_name = os.getenv('CON_ADB_DEV_C_CREDENTIAL_NAME')
    con_adb_dev_c_model           = os.getenv('CON_ADB_DEV_C_MODEL')

    # ADW23ai: Wallet
    con_adb_wallet_password     = os.getenv('CON_ADB_WALLET_PASSWORD')
    # Generative AI
    con_gen_ai_region           = config['region']
    con_gen_ai_service_endpoint = os.getenv('CON_GEN_AI_SERVICE_ENDPOINT')
    con_gen_ai_emb_model_url    = os.getenv('CON_GEN_AI_EMB_MODEL_URL')
    con_gen_ai_emb_model_id     = os.getenv('CON_GEN_AI_EMB_MODEL_ID')

    # Leer el archivo SQL
    with open(os.path.join(file_path, 'autonomous_database', user, file_name), 'r') as file:
        query = file.read()
    
    # .\autonomous_database\admin\a.CREATE_USER.sql
    query = query.replace('u_s_e_r_n_a_m_e', con_adb_dev_user_name)
    query = query.replace('p_a_s_s_w_o_r_d', con_adb_dev_password)
    
    # .\autonomous_database\developer\a.DBMS_VECTOR.sql
    query = query.replace('c_o_m_p_a_r_t_m_e_n_t__id', con_adb_dev_comparment_ocid)
    query = query.replace('u_s_e_r__o_c_i_d', con_adb_dev_c_user_ocid)
    query = query.replace('t_e_n_a_n_c_y__o_c_i_d', con_adb_dev_c_tenancy_ocid)
    query = query.replace('p_r_i_v_a_t_e__k_e_y', con_adb_dev_c_private_key)
    query = query.replace('f_i_n_g_e_r_p_r_i_n_t', con_adb_dev_c_fingerprint)
    query = query.replace('c_r_e_d_e_n_t_i_a_l__n_a_m_e', con_adb_dev_c_credential_name)

    # .\autonomous_database\developer\j.SP_VECTOR_STORE.sql
    query = query.replace('e_m_b__m_o_d_e_l__u_r_l', con_gen_ai_emb_model_url)
    query = query.replace('e_m_b__m_o_d_e_l__i_d', con_gen_ai_emb_model_id)
    
    # .\autonomous_database\developer\g.SP_SEL_AI_PROFILE.sql
    query = query.replace('r_e_g_i_o_n', con_gen_ai_region)
    query = query.replace('s_e_r_v_i_c_e__e_n_d_p_o_i_n_t', con_gen_ai_service_endpoint)
    query = query.replace('m_o_d_e_l', con_adb_dev_c_model)
    
    # Dividir en bloques PL/SQL si contiene el delimitador `--`
    statements = [stmt.strip() for stmt in query.split('--') if stmt.strip()]
    
    try:
        # Connection
        connection = oracledb.connect(
            user            = con_adb_adm_user_name if user=='admin' else con_adb_dev_user_name,
            password        = con_adb_adm_password if user=='admin' else con_adb_dev_password,
            dsn             = con_adb_adm_service_name if user=='admin' else con_adb_dev_service_name,
            config_dir      = wall_path,
            wallet_location = wall_path,
            wallet_password = con_adb_wallet_password
        )

        print(f'[Query]:')
        
        cursor = connection.cursor()
        for statement in statements:
            # Eliminar el último carácter si es un ';'
            if statement.endswith(';'):
                statement = statement[:-1].strip()
            
            if statement.endswith('/'):
                statement = statement[:-1].strip()
            
            print(f'  > {statement}\n')
            cursor.execute(statement)
        
        connection.commit()
        print(message)
    except oracledb.DatabaseError as e:
        error_msg = str(e)
        # Verificar si se produjo el error ORA-01920 al intentar crear el usuario
        if "ORA-01920" in error_msg and "CREATE_USER" in file_name:
            respuesta = input('The user already exists. Do you want to delete it to continue? (S/N): ')
            if respuesta.strip().lower() in ('', 's', 'si', 'y', 'yes'):
                # Ejecutar el script para eliminar el usuario (asegúrate de que 'a.DROP_USER.sql' exista en la carpeta correspondiente)
                exec('admin', 'a.DROP_USER.sql', '[OK][A] DROP USER DEVELOPER......................................[DROP_USER]')
                # Intentar nuevamente crear el usuario
                exec('admin', 'b.CREATE_USER.sql', '[OK][A] CREATE USER DEVELOPER................................[ CREATE_USER ]')
                return  # Salir de la función después de reintentar
            else:
                print("Installation cancelled.")
                sys.exit(1)
        else:
            print(f'[Error]:\n\n{e}')
            sys.exit(1)

def main():
    print(f'\n                                                       [ SETUP ][ ANACONDA ]')
    print(f'----------------------------------------------------------------------------')
    
    conda(f'conda --version', 
          f'[OK] CHECK CONDA.............................................[ CHECK_CONDA ]')

    conda(f'conda run -n base pip install --force-reinstall oci oracledb --upgrade --user', 
          f'[OK] PIP INSTALL OCI & ORACLEDB IN CONDA BASE.................[ CONDA_BASE ]')

    conda(f'conda run -n base pip install --force-reinstall python-dotenv --no-warn-script-location --upgrade --user', 
          f'[OK] PIP INSTALL PYTHON-DOTENV IN CONDA BASE..................[ CONDA_BASE ]')
    
    # Cargar variables del archivo .env
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=env_path)
    
    # CONFIG: CONDA
    con_conda_env_name    = os.getenv('CON_CONDA_ENV_NAME')
    # ADW23ai: Admin
    con_adb_adm_user_name = os.getenv('CON_ADB_ADM_USER_NAME')
    # ADW23ai: Developer
    con_adb_dev_user_name = os.getenv('CON_ADB_DEV_USER_NAME')

    conda(f'conda remove --name {con_conda_env_name} --all -y', 
          f'[OK] CONDA REMOVE......................................[ CONDA_ENVIRONMENT ]')
          
    conda(f'conda create -n {con_conda_env_name} python=3.10 -y', 
          f'[OK] CONDA CREATE ENVIRONMENT..........................[ CONDA_ENVIRONMENT ]')
    
    conda(f'conda run -n {con_conda_env_name} conda install -c conda-forge python-graphviz -y', 
          f'[OK] CONDA INSTALL GRAPHVIZ................................[ CONDA_INSTALL ]')
    
    conda(f'conda run -n {con_conda_env_name} pip install -r requirements.txt', 
          f'[OK] PIP INSTALL REQUIREMENTS..........................[ CONDA_ENVIRONMENT ]')
    
    print(f'\n                                                     [ VALIDATION ][ TOOLS ]')
    print(f'----------------------------------------------------------------------------')

    conda(f'python tool.config.py', 
          f'[OK] CONFIG FILE..............................................[ VALID_TOOL ]')
    
    conda(f'python tool.bucket.py', 
          f'[OK] BUCKET ACCESS............................................[ VALID_TOOL ]')
    
    conda(f'python tool.autonomos.connection.py', 
          f'[OK] AUTONOMOUS DATABASE CONNECTION...........................[ VALID_TOOL ]')

    print(f'\n                                            [ SETUP ][ AUTONOMOUS DATABASE ]')
    print(f'----------------------------------------------------------------------------')

    print(f'[USER: {con_adb_adm_user_name}]')
    
    exec('admin', 'b.CREATE_USER.sql',
        '[OK][B] CREATE USER DEVELOPER................................[ CREATE_USER ]')

    exec('admin', 'c.GRANT_USER.sql',
        '[OK][C] GRANT TO DEVELOPER....................................[ GRANT_USER ]')
    
    exec('admin', 'd.DBMS_NETWORK_ACL_ADMIN.sql',
        '[OK][D] APPEND_HOST_ACE...........................[ DBMS_NETWORK_ACL_ADMIN ]')
    
    print(f'\n[USER: {con_adb_dev_user_name}]')

    exec('developer', 'a.DBMS_VECTOR.sql',
        '[OK][A] DBMS_VECTOR.CREATE_CREDENTIAL........................[ DBMS_VECTOR ]')

    exec('developer', 'b.TABLE_USER_GROUP.sql',
        '[OK][B] CREATE TABLE USER_GROUP.............................[ CREATE_TABLE ]')    

    exec('developer', 'c.TABLE_USERS.sql',
        '[OK][C] CREATE TABLE USERS..................................[ CREATE_TABLE ]')

    exec('developer', 'd.TABLE_MODULES.sql',
        '[OK][D] CREATE TABLE MODULES................................[ CREATE_TABLE ]')

    exec('developer', 'e.TABLE_AGENT_MODELS.sql',
        '[OK][E] CREATE TABLE AGENT_MODELS...........................[ CREATE_TABLE ]')
    
    exec('developer', 'f.TABLE_AGENTS.sql',
        '[OK][F] CREATE TABLE AGENTS.................................[ CREATE_TABLE ]')

    exec('developer', 'g.TABLE_AGENT_USER.sql',
        '[OK][G] CREATE TABLE AGENT_USER.............................[ CREATE_TABLE ]')
    
    exec('developer', 'h.TABLE_FILES.sql',
        '[OK][H] CREATE TABLE FILES..................................[ CREATE_TABLE ]')

    exec('developer', 'i.TABLE_FILE_USER.sql',
        '[OK][I] CREATE TABLE FILE_USER..............................[ CREATE_TABLE ]')
    
    exec('developer', 'j.TABLE_DOCS.sql',
        '[OK][J] CREATE TABLE DOCS...................................[ CREATE_TABLE ]')

    exec('developer', 'k.SP_SEL_AI_TBL_CSV.sql',
        '[OK][K] CREATE PROCEDURE FOR SELECT AI [CSV]............[ CREATE_PROCEDURE ]')

    exec('developer', 'l.SP_SEL_AI_PROFILE.sql',
        '[OK][L] CREATE PROCEDURE FOR SELECT AI [PROFILE]......... CREATE_PROCEDURE ]')

    exec('developer', 'm.SP_SEL_AI_RAG_PROFILE.sql',
        '[OK][M] CREATE PROCEDURE FOR SELECT AI RAG [PROFILE]....[ CREATE_PROCEDURE ]')

    exec('developer', 'n.VW_DOCS_FILES.sql',
        '[OK][N] CREATE VIEW DOCS FOR VECTOS STORE....................[ CREATE_VIEW ]')

    exec('developer', 'o.SP_VECTOR_STORE.sql',
        '[OK][O] CREATE PROCEDURE VECTOS STORRE.......................[ CREATE_VIEW ]')
    
    # Copiar .streamlit (Windows: C:\Users\<usuario>\.streamlit, mac: /Users/<usuario>/.streamlit)
    source_streamlit = os.path.join(file_path, ".streamlit")
    dest_streamlit = os.path.join(os.path.expanduser("~"), ".streamlit")
    shutil.copytree(source_streamlit, dest_streamlit, dirs_exist_ok=True)
    
    # Streamlit
    os.chdir(os.path.normpath(os.path.abspath(os.path.join(os.getcwd(), "..", "app"))))
    conda(f'conda run -n {con_conda_env_name} streamlit run app.py --server.port 8501', 
          f'[OK] OPEN STREAMLIT (http://localhost:8501)..........................[ APP ]')
    
if __name__ == '__main__':
    main()

# CMD> conda deactivate
# CMD> conda remove --name ORACLE-AI --all -y