CREATE OR REPLACE VIEW vw_telco_last_bill_amount  AS
SELECT 
    c.customer_id AS customer_id,
    TO_CLOB(
        'El cliente ' || c.first_name || ' ' || c.last_name || 
        ' recibió su última factura el ' || TO_CHAR(lb.bill_date, 'YYYY-MM-DD') || 
        ' por un monto de ' || TO_CHAR(lb.bill_amount, '999,999.00') || ' dólares. ' ||
        'Este detalle es útil para identificar patrones de gasto del cliente.'
    ) AS EMBED_DATA,
    TO_CLOB(
        JSON_OBJECT(
            'case_name'   VALUE 'Last Bill Amount',
            'customer_id' VALUE c.customer_id,
            'bill_id'     VALUE lb.bill_id,
            'bill_date'   VALUE TO_CHAR(lb.bill_date, 'YYYY-MM-DD'),
            'bill_amount' VALUE TO_CHAR(lb.bill_amount, '999,999.00')
        )
    ) AS METADATA
FROM 
    telco_customers c
    JOIN telco_last_bill_amount lb ON c.customer_id = lb.customer_id