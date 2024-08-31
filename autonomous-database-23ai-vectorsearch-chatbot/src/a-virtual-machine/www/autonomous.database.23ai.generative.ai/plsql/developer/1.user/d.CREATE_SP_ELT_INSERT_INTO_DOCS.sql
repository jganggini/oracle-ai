CREATE OR REPLACE PROCEDURE sp_elt_insert_into_docs (
    p_industry  IN VARCHAR2,
    p_case_name IN VARCHAR2,
    p_view_name IN VARCHAR2
) AS
    v_sql_text   CLOB;
BEGIN
    -- Construir la sentencia SQL dinámica
    v_sql_text := 'INSERT INTO docs(ID, INDUSTRY, CASE_NAME, TEXT, EMBEDDING, METADATA) ' ||
                  'SELECT ds.customer_id AS ID, ' ||
                  '       ''' || p_industry || ''' AS INDUSTRY, ' ||
                  '       ''' || p_case_name || ''' AS CASE_NAME, ' ||
                  '       TO_CLOB(ct.chunk_data) AS TEXT, ' ||
                  '       TO_VECTOR(et.embed_vector) AS EMBEDDING, ' ||
                  '       ds.metadata AS METADATA ' ||
                  'FROM ' || p_view_name || ' ds, ' ||
                  '     dbms_vector_chain.utl_to_chunks( ' ||
                  '         ds.embed_data, ' ||
                  '         json(''{' || 
                  '           "by":"words",' || 
                  '           "max":"100",' || 
                  '           "overlap":"10",' || 
                  '           "split":"recursively",' || 
                  '           "language":"spanish",' || 
                  '           "normalize":"all"' || 
                  '         }'')' ||
                  '     ) c, ' ||
                  '     JSON_TABLE( ' ||
                  '         c.column_value, ''$[*]'' ' ||
                  '         COLUMNS ( ' ||
                  '             chunk_id     NUMBER         PATH ''$.chunk_id'', ' || 
                  '             chunk_offset NUMBER         PATH ''$.chunk_offset'', ' || 
                  '             chunk_length NUMBER         PATH ''$.chunk_length'', ' || 
                  '             chunk_data   VARCHAR2(4000) PATH ''$.chunk_data'' ' ||
                  '         ) ' ||
                  '     ) ct, ' ||
                  '     dbms_vector_chain.utl_to_embeddings( ' ||
                  '         ct.chunk_data, ' ||
                  '         json(''{' || 
                  '             "provider": "ocigenai",' || 
                  '             "credential_name": "OCI_CRED",' || 
                  '             "url": "https://inference.generativeai.us-chicago-1.oci.oraclecloud.com/20231130/actions/embedText",' || 
                  '             "model": "cohere.embed-multilingual-v3.0"' || 
                  '         }'')' ||
                  '     ) e, ' ||
                  '     JSON_TABLE( ' ||
                  '         e.column_value, ''$[*]'' ' ||
                  '         COLUMNS ( ' ||
                  '             embed_id     NUMBER         PATH ''$.embed_id'', ' || 
                  '             embed_data   VARCHAR2(4000) PATH ''$.embed_data'', ' || 
                  '             embed_vector CLOB           PATH ''$.embed_vector'' ' ||
                  '         ) ' ||
                  '     ) et ' ||
                  'WHERE NOT EXISTS ( ' ||
                  '    SELECT 1 FROM docs d ' ||
                  '    WHERE d.id = ds.customer_id ' ||
                  '      AND d.industry = ''' || p_industry || ''' ' ||
                  '      AND d.case_name = ''' || p_case_name || ''' ' ||
                  ')';

    EXECUTE IMMEDIATE v_sql_text;

    COMMIT;
EXCEPTION
    WHEN OTHERS THEN
        ROLLBACK;
        RAISE;  -- Relevanta el error para que sea visible
END;