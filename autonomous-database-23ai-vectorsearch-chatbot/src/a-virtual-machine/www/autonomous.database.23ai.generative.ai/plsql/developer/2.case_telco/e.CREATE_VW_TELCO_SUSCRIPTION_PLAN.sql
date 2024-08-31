CREATE OR REPLACE VIEW vw_telco_subscription_plan AS
SELECT 
    c.customer_id AS customer_id,
    TO_CLOB(
        'El cliente ' || c.first_name || ' ' || c.last_name || 
        ' está suscrito al plan ' || sp.plan_name || 
        ', que comenzó el ' || TO_CHAR(sp.plan_start_date, 'YYYY-MM-DD') || 
        ' y finalizará el ' || TO_CHAR(sp.plan_end_date, 'YYYY-MM-DD') || 
        '. El costo mensual de este plan es de ' || TO_CHAR(sp.monthly_cost, '999,999.00') || ' dólares.'
    ) AS EMBED_DATA,
    TO_CLOB(
        JSON_OBJECT(
            'case_name'   VALUE 'Subscription Plan',
            'customer_id' VALUE c.customer_id,
            'plan_id'     VALUE sp.plan_id,
            'plan_name'   VALUE sp.plan_name,
            'start_date'  VALUE TO_CHAR(sp.plan_start_date, 'YYYY-MM-DD'),
            'end_date'    VALUE TO_CHAR(sp.plan_end_date, 'YYYY-MM-DD')
        )
    ) AS METADATA
FROM 
    telco_customers c
    JOIN telco_subscription_plan sp ON c.customer_id = sp.customer_id