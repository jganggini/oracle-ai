    CREATE TABLE modules (
        module_id           NUMBER NOT NULL,
        module_name         VARCHAR2(250) NOT NULL,
        module_folder       VARCHAR2(250),
        module_src_type     VARCHAR2(250),
        module_trg_type     VARCHAR2(250),
        module_vector_store NUMBER DEFAULT 0 NOT NULL,
        module_state        NUMBER DEFAULT 1 NOT NULL,
        module_date         TIMESTAMP(6) DEFAULT SYSDATE NOT NULL,
        CONSTRAINT pk_module_id PRIMARY KEY (module_id)
        ENABLE
    );
    --

    CREATE SEQUENCE module_id_seq START WITH 1 INCREMENT BY 1 NOCACHE
    --

    CREATE OR REPLACE TRIGGER trg_modules_id
        BEFORE INSERT ON modules
        FOR EACH ROW
        WHEN (NEW.module_id IS NULL)
    BEGIN
        :NEW.module_id := module_id_seq.NEXTVAL;
    END;
    /
    --

    INSERT INTO modules (module_id, module_name)
    VALUES (0, 'Administrator');
    --

    INSERT INTO modules (module_id, module_name, module_folder, module_src_type, module_trg_type)
    VALUES (1, 'Select AI', 'module-select-ai', 'CSV', 'Autonomous Database');
    --

    INSERT INTO modules (module_id, module_name, module_folder, module_src_type, module_trg_type)
    VALUES (2, 'Select AI RAG', 'module-select-ai-rag', 'TXT, HTML, DOC, JSON, XML', 'Autonomous Database');
    --
    
    INSERT INTO modules (module_id, module_name, module_folder, module_src_type, module_trg_type, module_vector_store)
    VALUES (3, 'AI Document Understanding', 'module-ai-document-understanding', 'PDF, JPG, PNG, TIFF', 'PDF, JSON', 1);
    --

    INSERT INTO modules (module_id, module_name, module_folder, module_src_type, module_trg_type, module_vector_store)
    VALUES (4, 'AI Speech to Text', 'module-ai-speech-to-text', 'M4A, MKV, MP3, MP4, OGA, OGG, WAV', 'TXT, SRT', 1);
    --

    INSERT INTO modules (module_id, module_name, module_folder, module_src_type, module_trg_type, module_vector_store)
    VALUES (5, 'AI Document Multimodal', 'module-ai-document-multimodal', 'JPEG, PNG', 'MD', 1);
    --

    INSERT INTO modules (module_id, module_name, module_folder, module_src_type, module_trg_type, module_vector_store)
    VALUES (6, 'AI Speech to Text Real-Time', 'module-ai-speech-to-realtime', 'JSON', 'TXT', 1);
    --