    CREATE TABLE agent_models (
        agent_model_id                NUMBER NOT NULL,
        agent_model_name              VARCHAR2(250) DEFAULT 'none' NOT NULL,
        agent_model_type              VARCHAR2(100) DEFAULT 'llm' NOT NULL,
        agent_model_provider          VARCHAR2(250) DEFAULT 'none' NOT NULL,
        agent_model_service_endpoint  VARCHAR2(500) DEFAULT 's_e_r_v_i_c_e__e_n_d_p_o_i_n_t' NOT NULL,
        agent_model_state             NUMBER DEFAULT 1 NOT NULL,
        agent_model_date              TIMESTAMP(6) DEFAULT SYSDATE NOT NULL,
        CONSTRAINT pk_agent_model_id PRIMARY KEY (agent_model_id)
        ENABLE
    );
    --

    CREATE SEQUENCE agent_model_id_seq START WITH 1 INCREMENT BY 1 NOCACHE
    --

    CREATE OR REPLACE TRIGGER trg_agent_model_id
        BEFORE INSERT ON agent_models
        FOR EACH ROW
        WHEN (NEW.agent_model_id IS NULL)
    BEGIN
        :NEW.agent_model_id := agent_model_id_seq.NEXTVAL;
    END;
    /
    --

    INSERT INTO agent_models (agent_model_id, agent_model_name, agent_model_type, agent_model_provider)
    VALUES (0, 'none', 'llm', 'none');
    --

    INSERT INTO agent_models (agent_model_id, agent_model_name, agent_model_type, agent_model_provider)
    VALUES (1, 'cohere.command-r-plus-08-2024', 'llm', 'cohere');
    --

    INSERT INTO agent_models (agent_model_id, agent_model_name, agent_model_type, agent_model_provider)
    VALUES (2, 'meta.llama-3.1-405b-instruct', 'llm', 'meta');
    --

    INSERT INTO agent_models (agent_model_id, agent_model_name, agent_model_type, agent_model_provider)
    VALUES (3, 'meta.llama-3.1-70b-instruct', 'llm', 'meta');
    --

    INSERT INTO agent_models (agent_model_id, agent_model_name, agent_model_type, agent_model_provider)
    VALUES (4, 'meta.llama-3.2-90b-vision-instruct', 'vlm', 'meta');
    --
    
    INSERT INTO agent_models (agent_model_id, agent_model_name, agent_model_type, agent_model_provider)
    VALUES (5, 'meta.llama-3.3-70b-instruct', 'llm', 'meta');
    --
    
    INSERT INTO agent_models (agent_model_id, agent_model_name, agent_model_type, agent_model_provider)
    VALUES (6, 'meta.llama-4-scout-17b-16e-instruct', 'vlm', 'meta');
    --

    INSERT INTO agent_models (agent_model_id, agent_model_name, agent_model_type, agent_model_provider)
    VALUES (7, 'meta.llama-4-maverick-17b-128e-instruct-fp8', 'vlm', 'meta');
    --
    
    INSERT INTO agent_models (agent_model_id, agent_model_name, agent_model_type, agent_model_provider)
    VALUES (8, 'xai.grok-3', 'llm', 'xai');
    --

    INSERT INTO agent_models (agent_model_id, agent_model_name, agent_model_type, agent_model_provider)
    VALUES (9, 'xai.grok-3-fast', 'llm', 'xai');
    --

    INSERT INTO agent_models (agent_model_id, agent_model_name, agent_model_type, agent_model_provider)
    VALUES (10, 'xai.grok-3-mini', 'llm', 'xai');
    --