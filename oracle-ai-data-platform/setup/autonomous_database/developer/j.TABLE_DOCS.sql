    CREATE TABLE docs(
        id         NUMBER,
        file_id    NUMBER,
        text       CLOB,
        metadata   CLOB,
        embedding  VECTOR NOT NULL,
        CONSTRAINT pk_doc_id     PRIMARY KEY (id),
        CONSTRAINT fk_docs_files FOREIGN KEY (file_id) REFERENCES files(file_id)
        ENABLE
    );
    --

    CREATE SEQUENCE doc_id_seq START WITH 1 INCREMENT BY 1 NOCACHE;
    --

    CREATE OR REPLACE TRIGGER trg_docs_id
        BEFORE INSERT ON docs
        FOR EACH ROW
        WHEN (NEW.id IS NULL)
    BEGIN
        :NEW.id := doc_id_seq.NEXTVAL;
    END;
    /
    --

    CREATE VECTOR INDEX docs_hnsw_idx ON docs(embedding) ORGANIZATION NEIGHBOR PARTITIONS
    DISTANCE COSINE
    WITH TARGET ACCURACY 95;
    --