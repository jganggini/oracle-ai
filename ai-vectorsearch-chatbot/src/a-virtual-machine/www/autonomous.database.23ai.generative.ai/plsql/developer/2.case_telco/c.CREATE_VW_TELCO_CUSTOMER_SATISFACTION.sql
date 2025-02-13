CREATE OR REPLACE VIEW vw_telco_customer_satisfaction AS
SELECT 
    c.customer_id AS customer_id,
    TO_CLOB(
        'El cliente ' || c.first_name || ' ' || c.last_name || 
        ' otorgó una puntuación de satisfacción de ' || TO_CHAR(cs.satisfaction_score, '9.0') || 
        ' en la encuesta realizada el ' || TO_CHAR(cs.survey_date, 'YYYY-MM-DD') || 
        ' su correo electronico es ' || c.email || 
        '. Esta calificación es crítica para medir la retención del cliente y su experiencia general con los servicios.'
    ) AS EMBED_DATA,
    TO_CLOB(
        JSON_OBJECT(
            'case_name'          VALUE 'Customer Satisfaction',
            'customer_id'        VALUE c.customer_id,
            'satisfaction_id'    VALUE cs.satisfaction_id,
            'satisfaction_score' VALUE TO_CHAR(cs.satisfaction_score, '9.0'),
            'survey_date'        VALUE TO_CHAR(cs.survey_date, 'YYYY-MM-DD')
        )
    ) AS METADATA
FROM 
    telco_customers c
    JOIN telco_customer_satisfaction cs ON c.customer_id = cs.customer_id