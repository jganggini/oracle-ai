    CREATE TABLE users (
        user_id               NUMBER NOT NULL,
        user_username         VARCHAR2(250) NOT NULL,
        user_password         VARCHAR2(500) NOT NULL,
        user_sel_ai_password  VARCHAR2(500) NOT NULL,
        user_name             VARCHAR2(500) NOT NULL,
        user_last_name        VARCHAR2(500) NOT NULL,
        user_email            VARCHAR2(500) NOT NULL,
        user_modules          CLOB CHECK (user_modules IS JSON),
        user_state            NUMBER DEFAULT 1 NOT NULL,
        user_date             TIMESTAMP(6) DEFAULT SYSDATE NOT NULL,
        CONSTRAINT user_id_pk PRIMARY KEY (user_id)
        ENABLE
    );
    --

    CREATE UNIQUE INDEX user_username_unq ON users (user_username ASC);
    --

    CREATE SEQUENCE user_id_seq START WITH 1 INCREMENT BY 1 NOCACHE;
    --

    CREATE OR REPLACE TRIGGER trg_users_id
        BEFORE INSERT ON users
        FOR EACH ROW
        WHEN (NEW.user_id IS NULL)
    BEGIN
        :NEW.user_id := user_id_seq.NEXTVAL;
    END;
    /
    --

    INSERT INTO users (
        user_id,
        user_username,
        user_password,
        user_sel_ai_password,
        user_name,
        user_last_name,
        user_email,
        user_modules
    ) VALUES (
        0,
        'admin', 
        'admin',
        'p_a_s_s_w_o_r_d',
        'Joel', 
        'Ganggini', 
        'joel.ganggini@oracle.com',
        '[0, 1, 2, 3, 4, 5]'
    );
    --