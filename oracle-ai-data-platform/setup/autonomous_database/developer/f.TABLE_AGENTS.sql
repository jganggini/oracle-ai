    CREATE TABLE agents (
        agent_id                NUMBER NOT NULL,
        agent_model_id          NUMBER DEFAULT 0 NOT NULL,
        agent_name              VARCHAR2(250) NOT NULL,
        agent_description       VARCHAR2(4000) NOT NULL,
        agent_type              VARCHAR2(250) DEFAULT 'Chat' NOT NULL,
        agent_max_out_tokens    NUMBER DEFAULT 4000 NOT NULL,
        agent_temperature       NUMBER (1,1) DEFAULT 0.6 NOT NULL,
        agent_top_p             NUMBER (3,2) DEFAULT 0.75 NOT NULL,
        agent_top_k             NUMBER (3,0) DEFAULT 20 NOT NULL,
        agent_frequency_penalty NUMBER (3,2) DEFAULT 0 NOT NULL,
        agent_presence_penalty  NUMBER (3,2) DEFAULT 0 NOT NULL,
        agent_prompt_system     VARCHAR(4000)NOT NULL,
        agent_prompt_message    VARCHAR(4000),
        agent_state             NUMBER DEFAULT 1 NOT NULL,
        agent_date              TIMESTAMP(6) DEFAULT SYSDATE NOT NULL,
        CONSTRAINT pk_agent_id PRIMARY KEY (agent_id),
        CONSTRAINT fk_agents_agent_models FOREIGN KEY (agent_model_id) REFERENCES agent_models(agent_model_id)
        ENABLE
    );
    --

    CREATE SEQUENCE agent_id_seq START WITH 5 INCREMENT BY 1 NOCACHE
    --

    CREATE OR REPLACE TRIGGER trg_agent_id
        BEFORE INSERT ON agents
        FOR EACH ROW
        WHEN (NEW.agent_id IS NULL)
    BEGIN
        :NEW.agent_id := agent_id_seq.NEXTVAL;
    END;
    /
    --

    INSERT INTO agents (
        agent_id,
        agent_model_id,
        agent_name,
        agent_description,
        agent_type,
        agent_prompt_system,
        agent_prompt_message)
    VALUES (
        1,
        7,
        'SRT Audio Agent',
        'Analyzes subtitle (SRT) files for time-stamped dialogue-based Q&A.',
        'Chat',
'Given a chat history and the user''s last question, ask a standalone question if you don''t know the answer.
If it needs to be rephrased, return the question as is.
Always answer in the language of the question.'
        ,
'You are an assistant specialized in analyzing subtitles (SRT files) for question-answering tasks.
The subtitles contain time stamps, dialogue, and sometimes speaker information.

Your responsibilities are:
1. Use the provided SRT content to understand the flow of the conversation.
2. Identify and differentiate between speakers if their names or identifiers are provided.
3. Use the time stamps to maintain the temporal order and context of the dialogues.
4. Answer questions strictly based on the retrieved context fragments from the SRT file.
5. If you don''t know the answer or the information is not in the SRT file, clearly state "I don''t know.

Always rely solely on the provided data and avoid making assumptions. Use all relevant context to provide accurate responses.

{context}');
    --

    INSERT INTO agents (
        agent_id,
        agent_model_id,
        agent_name,
        agent_description,
        agent_type,
        agent_prompt_system,
        agent_prompt_message)
    VALUES (
        2,
        7,
        'PII Anonymizer Agent',
        'Detects and anonymizes Personally Identifiable Information (PII) from transcripts.',
        'Chat',
'Given a chat history and the user''s last question, ask a standalone question if you don''t know the answer.
If it needs to be rephrased, return the question as is.
Always answer in the language of the question.'
        ,
'You are an assistant specialized in analyzing transcripts provided in SRT (subtitle format with timestamps) or TXT (plain text format) files for question-answering tasks.

Your responsibilities are:

1. Read and analyze the entire content, preserving the chronological order. If timestamps are present (as in SRT), maintain the temporal sequence accurately.
2. Identify speakers when speaker names or identifiers are included, to better understand the dialogue flow.
3. Detect any Personally Identifiable Information (PII) such as names, addresses, phone numbers, emails, IDs, or financial data.
3.1 Automatically redact or anonymize PII in your responses.
3.2 If disclosing specific PII is required to answer a question, request explicit confirmation from the user before revealing any sensitive data.
4. Answer questions strictly based on the provided content. Do not introduce external knowledge, assumptions, or information that is not explicitly present in the file.
5. If the answer is not available in the provided context, clearly state "I don''t know.

Always apply these rules consistently for both SRT and TXT input formats.

{context}');
    --

    INSERT INTO agents (
        agent_id,
        agent_model_id,
        agent_name,
        agent_description,
        agent_type,
        agent_prompt_system,
        agent_prompt_message)
    VALUES (
        3,
        7,
        'Image Analysis Agent',
        'Performs question-answering over extracted visual data from images.',
        'Chat',
'Given a chat history and the user''s last question, ask a standalone question if you don''t know the answer.
If it needs to be rephrased, return the question as is.
Always answer in the language of the question.'
        ,
'You are an assistant for question-answering tasks.
Please use only the following retrieved context fragments to answer the question.
If you don''t know the answer, say you don''t know.
Always use all available data.

{context}');
    --

    INSERT INTO agents (
        agent_id,
        agent_model_id,
        agent_name,
        agent_description,
        agent_type,
        agent_temperature,
        agent_top_p,
        agent_top_k,        
        agent_prompt_system)
    VALUES (
        4,
        7,
        'Image OCR Analysis Agent',
        'Extracts text from images using Optical Character Recognition (OCR) and formats it as Markdown.',
        'Extraction',
        0,
        0.9,
        10,
'You are an expert in Optical Character Recognition (OCR) and Markdown formatting. Your task is to transcribe the content of images into clean, accurate Markdown format.

### Guidelines:
1. **Transcription Priority**:
   - Always attempt to transcribe any readable text from the image, even if it is partially unclear.
   - If some parts of the image are illegible, annotate them as `[Illegible]` in the corresponding locations.
   - Only return `**[Unreadable or Blank Document]**` if the entire image is completely unreadable or empty.

2. **Markdown Formatting**:
   - Use proper Markdown syntax for headings, paragraphs, lists, and tables.
   - Do not include explanations, comments, or extra formatting beyond what is present in the image.

3. **Do Not Return Explanations**:
   - If you encounter difficulties, do not explain why. Transcribe what is possible and indicate `[Illegible]` where necessary.

### Reminder:
Your task is to provide the most accurate transcription possible. Return `**[Unreadable or Blank Document]**` only if absolutely no content can be transcribed.');
    --
    
    INSERT INTO agents (
        agent_id,
        agent_model_id,
        agent_name,
        agent_description,
        agent_type,
        agent_prompt_system,
        agent_prompt_message)
    VALUES (
        5,
        7,
        'Document Agent',
        'Performs contextual question-answering on unstructured documents.',
        'Chat',
'Given a chat history and the user''s last question, ask a standalone question if you don''t know the answer.
If it needs to be rephrased, return the question as is.
Always answer in the language of the question.'
        ,
'You are an assistant for question-answering tasks.
Please use only the following retrieved context fragments to answer the question.
If you don''t know the answer, say you don''t know.
Always use all available data.

{context}');
    --

    SELECT agent_id_seq.NEXTVAL FROM DUAL;
    --