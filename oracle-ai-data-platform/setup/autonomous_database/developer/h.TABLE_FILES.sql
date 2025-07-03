    CREATE TABLE files (
        file_id                  NUMBER NOT NULL,
        module_id                NUMBER NOT NULL,
        file_src_file_name       VARCHAR2(500) NOT NULL,
        file_src_size            NUMBER DEFAULT 0 NOT NULL,
        file_src_strategy        VARCHAR2(500) DEFAULT 'None' NOT NULL,
        file_trg_obj_name        VARCHAR2(4000) DEFAULT 'None' NOT NULL,
        file_trg_extraction      CLOB NULL,
        file_trg_tot_pages       NUMBER DEFAULT 1 NOT NULL,
        file_trg_tot_characters  NUMBER DEFAULT 0 NOT NULL,
        file_trg_tot_time        VARCHAR2(8) DEFAULT '00:00:00' NOT NULL,
        file_trg_language        VARCHAR2(3) DEFAULT 'esa' NOT NULL,
        file_trg_pii             NUMBER DEFAULT 0 NOT NULL,
        file_description         VARCHAR2(500) NOT NULL,
        file_version             NUMBER DEFAULT 1 NOT NULL,
        file_state               NUMBER DEFAULT 1 NOT NULL,
        file_date                TIMESTAMP(6) DEFAULT SYSDATE NOT NULL,        
        CONSTRAINT pk_file_id PRIMARY KEY (file_id)
        ENABLE
    );
    --

    CREATE SEQUENCE file_id_seq START WITH 1 INCREMENT BY 1 NOCACHE;
    --

    CREATE OR REPLACE TRIGGER trg_files_id
        BEFORE INSERT ON files
        FOR EACH ROW
        WHEN (NEW.file_id IS NULL)
    BEGIN
        :NEW.file_id := file_id_seq.NEXTVAL;
    END;
    /
    --