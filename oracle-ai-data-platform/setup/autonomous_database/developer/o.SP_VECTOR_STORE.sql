    CREATE OR REPLACE PROCEDURE SP_VECTOR_STORE (
       p_file_id IN NUMBER
    ) AS
    BEGIN
        DELETE FROM DOCS WHERE FILE_ID = p_file_id;
        COMMIT;
        
        INSERT INTO DOCS (FILE_ID, TEXT, METADATA, EMBEDDING)
        SELECT
            a.FILE_ID                  AS FILE_ID,
            TO_CLOB(ct.chunk_data)     AS TEXT,
            a.METADATA                 AS METADATA,
            TO_VECTOR(et.embed_vector) AS EMBEDDING
        FROM VW_DOCS_FILES a
            CROSS JOIN dbms_vector_chain.utl_to_chunks(
                a.TEXT,
                json('{
                    "by"        : "characters",
                    "max"       : "512",
                    "overlap"   : "51",
                    "split"     : "recursively",
                    "language"  : "'|| a.LANGUAGE ||'",
                    "normalize" : "all"
                }')
            ) c
            CROSS JOIN JSON_TABLE(
                c.column_value, '$[*]'
                COLUMNS (
                    chunk_id     NUMBER         PATH '$.chunk_id',
                    chunk_offset NUMBER         PATH '$.chunk_offset',
                    chunk_length NUMBER         PATH '$.chunk_length',
                    chunk_data   VARCHAR2(4000) PATH '$.chunk_data'
                )
            ) ct
            CROSS JOIN dbms_vector_chain.utl_to_embeddings(
                ct.chunk_data,
                json('{
                    "provider"        : "ocigenai",
                    "credential_name" : "c_r_e_d_e_n_t_i_a_l__n_a_m_e",
                    "url"             : "e_m_b__m_o_d_e_l__u_r_l",
                    "model"           : "e_m_b__m_o_d_e_l__i_d"
                }')
            ) e
            CROSS JOIN JSON_TABLE(
                e.column_value, '$[*]'
                COLUMNS (
                    embed_id     NUMBER         PATH '$.embed_id',
                    embed_data   VARCHAR2(4000) PATH '$.embed_data',
                    embed_vector CLOB           PATH '$.embed_vector'
                )
            ) et
        WHERE
            a.FILE_ID = p_file_id;
        COMMIT;
        
    END;
    /
    --