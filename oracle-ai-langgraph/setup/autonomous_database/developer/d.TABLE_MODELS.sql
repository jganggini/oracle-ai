    CREATE TABLE models (
        model_id                NUMBER NOT NULL,
        model_name              VARCHAR2(250) DEFAULT 'none' NOT NULL,
        model_type              VARCHAR2(100) DEFAULT 'llm' NOT NULL,
        model_provider          VARCHAR2(250) DEFAULT 'none' NOT NULL,
        model_service_endpoint  VARCHAR2(500) DEFAULT 's_e_r_v_i_c_e__e_n_d_p_o_i_n_t' NOT NULL,
        model_state             NUMBER DEFAULT 1 NOT NULL,
        model_date              TIMESTAMP(6) DEFAULT SYSDATE NOT NULL,
        CONSTRAINT model_id_pk PRIMARY KEY (model_id)
        ENABLE
    );
    --

    CREATE SEQUENCE model_id_seq START WITH 1 INCREMENT BY 1 NOCACHE
    --

    CREATE OR REPLACE TRIGGER trg_model_id
        BEFORE INSERT ON models
        FOR EACH ROW
        WHEN (NEW.model_id IS NULL)
    BEGIN
        :NEW.model_id := model_id_seq.NEXTVAL;
    END;
    /
    --

    INSERT INTO models (model_id, model_name, model_type, model_provider)
    VALUES (0, 'none', 'llm', 'none');
    --

    INSERT INTO models (model_id, model_name, model_type, model_provider)
    VALUES (1, 'cohere.command-r-plus-08-2024', 'llm', 'cohere');
    --