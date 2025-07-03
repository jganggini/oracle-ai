    CREATE TABLE agent_user (
        agent_user_id            NUMBER NOT NULL,
        agent_id                 NUMBER NOT NULL,
        user_id                  NUMBER NOT NULL,
        owner                    NUMBER DEFAULT 1 NOT NULL,
        agent_user_state         NUMBER DEFAULT 1 NOT NULL,
        agent_user_date          TIMESTAMP(6) DEFAULT SYSDATE NOT NULL,        
        CONSTRAINT pk_agent_user_id     PRIMARY KEY (agent_user_id),
        CONSTRAINT fk_agent_user_agents FOREIGN KEY (agent_id) REFERENCES agents(agent_id),
        CONSTRAINT fk_agent_user_users  FOREIGN KEY (user_id) REFERENCES users(user_id)
        ENABLE
    );
    --

    CREATE SEQUENCE agent_user_id_seq START WITH 1 INCREMENT BY 1 NOCACHE;
    --

    CREATE OR REPLACE TRIGGER trg_agent_user_id
        BEFORE INSERT ON agent_user
        FOR EACH ROW
        WHEN (NEW.agent_user_id IS NULL)
    BEGIN
        :NEW.agent_user_id := agent_user_id_seq.NEXTVAL;
    END;
    /
    --

    INSERT INTO agent_user (agent_id, user_id)
    VALUES (1, 0);
    --

    INSERT INTO agent_user (agent_id, user_id)
    VALUES (2, 0);
    --

    INSERT INTO agent_user (agent_id, user_id)
    VALUES (3, 0);
    --

    INSERT INTO agent_user (agent_id, user_id)
    VALUES (4, 0);
    --

    INSERT INTO agent_user (agent_id, user_id)
    VALUES (5, 0);
    --