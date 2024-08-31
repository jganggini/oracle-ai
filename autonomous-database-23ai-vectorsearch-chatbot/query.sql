INSERT INTO docs(ID, INDUSTRY, CASE_NAME, TEXT, EMBEDDING, METADATA)
SELECT A.customer_id             AS ID,
       :p_industry               AS INDUSTRY,
       :p_case_name              AS CASE_NAME,
       TO_CLOB(C.chunk_data)     AS TEXT,
       TO_VECTOR(E.embed_vector) AS EMBEDDING,
       A.metadata                AS METADATA
FROM vw_contract_type A,
    dbms_vector_chain.utl_to_chunks(
        A.embed_data,
        json('{
            "by":"words",
            "max":"100",
            "overlap":"10",
            "split":"recursively",
            "language":"spanish",
            "normalize":"all"
        }')
    ) B,
    JSON_TABLE(
        B.column_value, '$[*]' 
        COLUMNS (
            chunk_id     NUMBER         PATH '$.chunk_id', 
            chunk_offset NUMBER         PATH '$.chunk_offset', 
            chunk_length NUMBER         PATH '$.chunk_length', 
            chunk_data   VARCHAR2(4000) PATH '$.chunk_data'
        )
    ) C,
    dbms_vector_chain.utl_to_embeddings(
        C.chunk_data,
        json('{
                "provider": "ocigenai",
                "credential_name": "OCI_CRED",
                "url": "https://inference.generativeai.us-chicago-1.oci.oraclecloud.com/20231130/actions/embedText",
                "model": "cohere.embed-multilingual-v3.0"
            }')
    ) D,
    JSON_TABLE(
        D.column_value, '$[*]' 
        COLUMNS (
            embed_id     NUMBER         PATH '$.embed_id', 
            embed_data   VARCHAR2(4000) PATH '$.embed_data', 
            embed_vector CLOB           PATH '$.embed_vector'
        )
    ) E
WHERE NOT EXISTS (
    SELECT 1 FROM docs d
    WHERE d.id = A.customer_id
      AND d.industry  = :p_industry
      AND d.case_name = :p_case_name
);


