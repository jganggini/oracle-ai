BEGIN
    EXECUTE IMMEDIATE 'CREATE TABLE telco_customers (
        customer_id NUMBER PRIMARY KEY,
        first_name VARCHAR2(255),
        last_name VARCHAR2(255),
        email VARCHAR2(255),
        phone_number VARCHAR2(50),
        address VARCHAR2(255),
        city VARCHAR2(100),
        state VARCHAR2(100),
        postal_code VARCHAR2(50),
        country VARCHAR2(100)
    )';

    EXECUTE IMMEDIATE 'CREATE TABLE telco_subscription_plan (
        plan_id NUMBER PRIMARY KEY,
        customer_id NUMBER,
        plan_name VARCHAR2(255),
        plan_start_date DATE,
        plan_end_date DATE,
        monthly_cost NUMBER(10, 2),
        CONSTRAINT fk_customer_plan FOREIGN KEY (customer_id) REFERENCES telco_customers(customer_id)
    )';

    EXECUTE IMMEDIATE 'CREATE TABLE telco_contract_type (
        contract_id NUMBER PRIMARY KEY,
        customer_id NUMBER,
        contract_type VARCHAR2(20) CHECK (contract_type IN (''Prepaid'', ''Postpaid'', ''No Contract'')),
        CONSTRAINT fk_customer_contract FOREIGN KEY (customer_id) REFERENCES telco_customers(customer_id)
    )';

    EXECUTE IMMEDIATE 'CREATE TABLE telco_last_bill_amount (
        bill_id NUMBER PRIMARY KEY,
        customer_id NUMBER,
        bill_date DATE,
        bill_amount NUMBER(10, 2),
        CONSTRAINT fk_customer_bill FOREIGN KEY (customer_id) REFERENCES telco_customers(customer_id)
    )';

    EXECUTE IMMEDIATE 'CREATE TABLE telco_customer_satisfaction (
        satisfaction_id NUMBER PRIMARY KEY,
        customer_id NUMBER,
        satisfaction_score NUMBER(3, 1),
        survey_date DATE,
        CONSTRAINT fk_customer_satisfaction FOREIGN KEY (customer_id) REFERENCES telco_customers(customer_id)
    )';
END;