CREATE OR REPLACE VIEW vw_telco_customer_calls AS
SELECT 
    cc.call_id AS id,
    TO_CLOB(
        'El cliente ' || c.first_name || ' ' || c.last_name || 
        ' hizo una llamada el ' || TO_CHAR(cc.call_date, 'YYYY-MM-DD HH24:MI:SS') || 
        '. El texto de la llamada es: ' || cc.call_text || '. ' || 
        'Los sentimientos de las oraciones de la llamada fueron: ' || cc.call_sentiments_sentence_metric || '. ' ||
        'La puntuacion del análisis de sentimiento de la llamada fue: ' || cc.call_sentiments_sentence_score || '. ' ||
        'Con un puntaje de: ' || cc.call_sentiments_sentence_score || '.'
    ) AS EMBED_DATA,
    TO_CLOB(
        JSON_OBJECT(
            'case_name'     VALUE 'Customer Calls',
            'customer_id'   VALUE c.customer_id,
            'call_id'       VALUE cc.call_id,
            'customer_code' VALUE c.customer_code,
            'call_date'     VALUE TO_CHAR(cc.call_date, 'YYYY-MM-DD HH24:MI:SS')
        )
    ) AS METADATA
FROM
    telco_customers c
JOIN
    telco_customer_calls cc ON c.customer_id = cc.customer_id