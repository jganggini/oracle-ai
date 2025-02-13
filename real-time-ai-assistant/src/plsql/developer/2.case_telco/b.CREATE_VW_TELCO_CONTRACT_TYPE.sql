CREATE OR REPLACE VIEW vw_telco_contract_type AS
SELECT 
    c.customer_id AS id,
    c.customer_code AS customer_code,
    TO_CLOB(
        'El cliente ' || c.first_name || ' ' || c.last_name || 
        ' tiene un contrato de tipo ' || ct.contract_type || 
        ', lo cual puede ser relevante para ofrecer promociones específicas según su modalidad de contrato.'
    ) AS EMBED_DATA,
    TO_CLOB(
        JSON_OBJECT(
            'case_name'     VALUE 'Contract Type',
            'customer_id'   VALUE c.customer_id,
            'contract_id'   VALUE ct.contract_id,            
            'contract_type' VALUE ct.contract_type
        )
    ) AS METADATA
FROM 
    telco_customers c
JOIN 
    telco_contract_type ct ON c.customer_id = ct.customer_id
