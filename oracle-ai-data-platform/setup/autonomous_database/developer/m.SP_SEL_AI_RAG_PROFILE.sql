    CREATE OR REPLACE PROCEDURE SP_SEL_AI_RAG_PROFILE (
        p_profile_name IN VARCHAR2,
        p_index_name   IN VARCHAR2,
        p_location     IN VARCHAR2
    )
    AS
        l_model           VARCHAR2(255)  := 'm_o_d_e_l';
        l_credential      VARCHAR2(4000) := 'c_r_e_d_e_n_t_i_a_l__n_a_m_e';
        l_json_attributes CLOB;
    BEGIN
        /* 1) Drop the profile if it exists */
        DBMS_CLOUD_AI.DROP_PROFILE(profile_name => p_profile_name, force => TRUE);

        /* Create a new profile */
        DBMS_CLOUD_AI.CREATE_PROFILE(
            profile_name => p_profile_name,
            attributes   => '{
                "provider":"oci", 
                "credential_name":"' || l_credential || '", 
                "vector_index_name":"' || p_index_name || '",
                "max_tokens":4000, 
                "model": "' || l_model || '" 
            }'
        );

        /* 2) Construct attributes for vector index */
        l_json_attributes := '{
            "vector_db_provider":"oracle", 
            "location":"' || p_location || '", 
            "object_storage_credential_name": "' || l_credential || '",
            "profile_name":"' || p_profile_name || '",
            "vector_dimension":1024,
            "vector_distance_metric":"cosine",
            "chunk_overlap":128,
            "chunk_size":1024
        }';
        
        /* 3) Drop vector index if it exists */
        DBMS_CLOUD_AI.DROP_VECTOR_INDEX(index_name   => p_index_name, include_data => TRUE, force => TRUE);
        
        /* 4) Create the vector index */
        DBMS_CLOUD_AI.CREATE_VECTOR_INDEX(
            index_name  => p_index_name,
            attributes  => l_json_attributes
        );

    END;
    /
    --