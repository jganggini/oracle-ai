    CREATE TABLE file_user (
        file_user_id             NUMBER NOT NULL,
        file_id                  NUMBER NOT NULL,
        user_id                  NUMBER NOT NULL,
        owner                    NUMBER DEFAULT 1 NOT NULL,
        file_user_state          NUMBER DEFAULT 1 NOT NULL,
        file_user_date           TIMESTAMP(6) DEFAULT SYSDATE NOT NULL,        
        CONSTRAINT pk_file_user_id    PRIMARY KEY (file_user_id),
        CONSTRAINT fk_file_user_files FOREIGN KEY (file_id) REFERENCES files(file_id),
        CONSTRAINT fk_file_user_users FOREIGN KEY (user_id) REFERENCES users(user_id)
        ENABLE
    );
    --

    CREATE SEQUENCE file_user_id_seq START WITH 1 INCREMENT BY 1 NOCACHE;
    --

    CREATE OR REPLACE TRIGGER trg_file_user_id
        BEFORE INSERT ON file_user
        FOR EACH ROW
        WHEN (NEW.file_user_id IS NULL)
    BEGIN
        :NEW.file_user_id := file_user_id_seq.NEXTVAL;
    END;
    /
    --