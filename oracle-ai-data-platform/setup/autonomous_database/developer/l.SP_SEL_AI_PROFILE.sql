    CREATE OR REPLACE PROCEDURE SP_SEL_AI_PROFILE (
        p_profile_name IN VARCHAR2,
        p_user_id      IN NUMBER
    )
    AS
        l_model           VARCHAR2(255)  := 'm_o_d_e_l';
        l_credential      VARCHAR2(4000) := 'c_r_e_d_e_n_t_i_a_l__n_a_m_e';
        l_region          VARCHAR2(255)  := 'r_e_g_i_o_n';
        l_compartment_id  VARCHAR2(255)  := 'c_o_m_p_a_r_t_m_e_n_t__id';
        l_object_list     CLOB;
        l_json_attributes CLOB;
        CURSOR c_objects IS
            SELECT 
                SUBSTR(F.FILE_TRG_OBJ_NAME, 1, INSTR(F.FILE_TRG_OBJ_NAME, '.') - 1) AS owner,
                SUBSTR(F.FILE_TRG_OBJ_NAME, INSTR(F.FILE_TRG_OBJ_NAME, '.') + 1) AS name
            FROM FILES F
            JOIN FILE_USER FU ON F.FILE_ID = FU.FILE_ID
            WHERE F.FILE_STATE = 1
            AND F.MODULE_ID = 1
            AND FU.USER_ID = p_user_id;
    BEGIN
        /* 1) Drop the profile if it exists */
        DBMS_CLOUD_AI.DROP_PROFILE(profile_name => p_profile_name, force => TRUE);

        /* 2) Build object_list JSON array from FILES table */
        l_object_list := '[';
        FOR rec IN c_objects LOOP
            l_object_list := l_object_list || '{"owner": "' || rec.owner || '", "name": "' || rec.name || '"},';
        END LOOP;

        /* Remove trailing comma and close JSON array */
        IF l_object_list LIKE '%,' THEN
            l_object_list := SUBSTR(l_object_list, 1, LENGTH(l_object_list) - 1);
        END IF;
        l_object_list := l_object_list || ']';
        
        /* 3) Construct the JSON attributes */
        l_json_attributes := '{
            "provider":"oci",
            "model":"' || l_model || '",
            "credential_name":"' || l_credential || '",
            "comments":"true",
            "object_list": ' || l_object_list || ',
            "region":"' || l_region || '",
            "oci_compartment_id": "' || l_compartment_id || '"
        }';

        /* 4) Create the profile */
        DBMS_CLOUD_AI.CREATE_PROFILE(
            profile_name => p_profile_name,
            attributes   => l_json_attributes
        );
    END;
    /
    --