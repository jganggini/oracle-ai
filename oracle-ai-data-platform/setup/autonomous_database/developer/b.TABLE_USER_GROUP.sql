    CREATE TABLE user_group (
        user_group_id           NUMBER NOT NULL,
        user_group_name         VARCHAR2(250) NOT NULL,
        user_group_description  VARCHAR2(500) NOT NULL,        
        user_group_state        NUMBER DEFAULT 1 NOT NULL,
        user_group_date         TIMESTAMP(6) DEFAULT SYSDATE NOT NULL,
        CONSTRAINT pk_user_group_id PRIMARY KEY (user_group_id)
        ENABLE
    );
    --

    CREATE SEQUENCE user_group_id_seq START WITH 1 INCREMENT BY 1 NOCACHE;
    --

    CREATE OR REPLACE TRIGGER trg_user_group_id
        BEFORE INSERT ON user_group
        FOR EACH ROW
        WHEN (NEW.user_group_id IS NULL)
    BEGIN
        :NEW.user_group_id := user_group_id_seq.NEXTVAL;
    END;
    /
    --

    INSERT INTO user_group (
        user_group_id,
        user_group_name,
        user_group_description
    ) VALUES (
        0,
        'Administrators',
        'Administrator Group'
    );
    --

    SELECT user_group_id_seq.NEXTVAL FROM DUAL;
    --