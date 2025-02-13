CREATE TABLE docs(
    id         NUMBER,
    industry   VARCHAR2(500),
    case_name  VARCHAR2(500),
    text       CLOB,
    metadata   CLOB,
    embedding  VECTOR NOT NULL
)