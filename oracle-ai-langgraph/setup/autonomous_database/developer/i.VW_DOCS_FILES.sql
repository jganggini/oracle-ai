    CREATE OR REPLACE VIEW VW_DOCS_FILES AS
    SELECT
        a.FILE_ID             AS FILE_ID,
        a.FILE_TRG_EXTRACTION AS TEXT,
        TO_CLOB(
            JSON_OBJECT(
                'file_id'            VALUE a.FILE_ID,
                'file_src_file_name' VALUE a.FILE_SRC_FILE_NAME,
                'file_trg_obj_name'  VALUE a.FILE_TRG_OBJ_NAME,
                'file_version'       VALUE a.FILE_VERSION,
                'file_date'          VALUE TO_CHAR(a.FILE_DATE, 'YYYY-MM-DD HH24:MI:SS'),
                'obj_name'           VALUE REGEXP_SUBSTR(a.FILE_TRG_OBJ_NAME, '[^/]+$', 1, 1),
                'user_id'            VALUE a.USER_ID,
                'user_username'      VALUE b.USER_USERNAME,
                'module_id'          VALUE a.MODULE_ID,
                'module_name'        VALUE c.MODULE_NAME
            )
        ) AS METADATA,
        a.FILE_TRG_LANGUAGE AS LANGUAGE
    FROM
        FILES a
    JOIN
        users b
        ON a.USER_ID = b.USER_ID
    JOIN
        modules c
        ON a.MODULE_ID = c.MODULE_ID
    WHERE
        a.FILE_STATE = 1
        AND c.MODULE_VECTOR_STORE = 1
    /
    --