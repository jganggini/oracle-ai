CREATE OR REPLACE VIEW vw_telco_chaims_resolution_option AS
SELECT 
    resolution_option_id AS id,
    TO_CLOB(
        'La opción de resolución con ID ' || resolution_option_id || 
        ' es de tipo "' || resolution_type || '". ' || 
        'Esta opción ofrece: ' || description || 
        ' aplicable al producto: ' || applicable_product || 
        '. ' || 
        CASE
            WHEN discount_value > 0 THEN 'Incluye un descuento de ' || TO_CHAR(discount_value, '999.99') || '%. '
            ELSE 'No incluye descuentos adicionales. '
        END ||
        'Notas adicionales: ' || resolution_notes || '.'
    ) AS EMBED_DATA,
    TO_CLOB(
        JSON_OBJECT(
            'case_name'            VALUE 'Claim Resolution Option',
            'resolution_option_id' VALUE resolution_option_id,
            'resolution_type'      VALUE resolution_type,
            'description'          VALUE description,
            'discount_value'       VALUE TO_CHAR(discount_value, '999.99'),
            'applicable_product'   VALUE applicable_product,
            'resolution_notes'     VALUE resolution_notes
        )
    ) AS METADATA
FROM 
    telco_claim_resolution_options