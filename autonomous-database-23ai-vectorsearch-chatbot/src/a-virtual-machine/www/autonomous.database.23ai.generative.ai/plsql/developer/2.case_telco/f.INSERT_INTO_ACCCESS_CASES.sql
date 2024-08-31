BEGIN
    -- Array of records to be inserted into the access_cases table
    FOR rec IN (
        SELECT 'TELCO' AS industry, 'Contract Type' AS case_name, 'vw_telco_contract_type' AS view_name, 'Contract Manager' AS profile FROM dual
        UNION ALL
        SELECT 'TELCO', 'Customer Satisfaction', 'vw_telco_customer_satisfaction', 'Service Lead' FROM dual
        UNION ALL
        SELECT 'TELCO', 'Last Bill Amount', 'vw_telco_last_bill_amount', 'Billing Specialist' FROM dual
        UNION ALL
        SELECT 'TELCO', 'Contract Type', 'vw_telco_contract_type', 'Product Manager' FROM dual
        UNION ALL
        SELECT 'TELCO', 'Customer Satisfaction', 'vw_telco_customer_satisfaction', 'Product Manager' FROM dual
        UNION ALL
        SELECT 'TELCO', 'Last Bill Amount', 'vw_telco_last_bill_amount', 'Product Manager' FROM dual
        UNION ALL
        SELECT 'TELCO', 'Subscription Plan', 'vw_telco_subscription_plan', 'Product Manager' FROM dual
    ) LOOP
        INSERT INTO access_cases (industry, case_name, view_name, profile)
        VALUES (rec.industry, rec.case_name, rec.view_name, rec.profile);
    END LOOP;
    
    COMMIT;
END;