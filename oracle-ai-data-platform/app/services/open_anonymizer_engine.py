import os
import oci

from dotenv import load_dotenv
import components as component
import services as service
import services.database as database
import utils as utils

from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine
from presidio_analyzer.predefined_recognizers.phone_recognizer import PhoneRecognizer

# Initialize services
config               = oci.config.from_file(profile_name=os.getenv('CON_OCI_PROFILE_NAME', 'DEFAULT'))
bucket_service       = service.BucketService()
utl_function_service = utils.FunctionService()
db_file_service      = database.FileService()
db_doc_service       = database.DocService()
language_map         = {
    "Spanish"    : "es",
    "Portuguese" : "pt",
    "English"    : "en"
}

load_dotenv()

class AnalyzerEngineService:
    
    @staticmethod
    def create(
            object_name,
            language,
            file_id,
            text,
            trg_type
        ):
        try:
            # Configura spaCy para español
            nlp_config = {
                "nlp_engine_name": "spacy",
                "models": [{"lang_code": "es", "model_name": "es_core_news_md"}],
            }
            nlp_engine = NlpEngineProvider(nlp_configuration=nlp_config).create_engine()

            # Pass created NLP engine and supported_languages to the AnalyzerEngine
            analyzer = AnalyzerEngine(
                nlp_engine=nlp_engine,
                supported_languages=["es"],
            )

            # Añade el recognizer de teléfonos
            phone_rec = PhoneRecognizer(
                supported_language="es",
                supported_regions=["PE", "CL", "CO", "AR", "MX"],
                leniency=1,
            )
            analyzer.registry.add_recognizer(phone_rec)

            # Crea y registra el recognizer para DNI peruano
            dni_patterns = [
                Pattern(
                    name="DNI Perú",
                    regex=r"\b(?:\d[\s-]?){8}\b",
                    score=0.85,
                )
            ]
            dni_recognizer = PatternRecognizer(
                supported_entity="IDENTIFIER",
                patterns=dni_patterns,
                supported_language="es",
            )
            analyzer.registry.add_recognizer(dni_recognizer)

            # Crea y registra el recognizer para código bancario
            bank_patterns = [
                Pattern(
                    name="Código bancario Perú",
                    regex=r"\b(?:\d{1,4}[\s-]?){4,10}\b",
                    score=0.85,
                )
            ]
            bank_recognizer = PatternRecognizer(
                supported_entity="NUMBER",
                patterns=bank_patterns,
                supported_language="es",
            )
            analyzer.registry.add_recognizer(bank_recognizer)

            data = None
            blocks = []

            # Clear
            if trg_type == "SRT":
                blocks = utl_function_service.parse_srt_blocks(text)

                # Inicializa Anonymizer
                anonymizer = AnonymizerEngine()
                anonymized_blocks = []

                for idx, ts, block_text in blocks:
                    normalized_text = utl_function_service.normalize_obfuscated_email(block_text)

                    # Analiza individualmente el bloque (puede tener múltiples líneas)
                    results = analyzer.analyze(
                        text=normalized_text,
                        entities=[
                            "PERSON",
                            "LOCATION",
                            "PHONE_NUMBER",
                            "EMAIL_ADDRESS",
                            "IDENTIFIER",
                            "NUMBER",
                        ],
                        language="es",
                    )

                    # Anonimiza el texto del bloque
                    anonymized = anonymizer.anonymize(text=normalized_text, analyzer_results=results)
                    anonymized_blocks.append((idx, ts, anonymized.text))

                # Reconstruir el archivo SRT con saltos originales
                reconstructed_srt = []
                for idx, ts, anon_text in anonymized_blocks:
                    reconstructed_srt.append(f"{idx}\n{ts}\n{anon_text}\n")

                final_srt_text = "\n".join(reconstructed_srt).strip()

                # Extraer path y nombre de archivo
                base_path, file_name = object_name.rsplit("/", 1)
                file_name = file_name.rsplit(".", 1)[0]

                # Resultado final
                data = final_srt_text
                
                # Upload file to Bucket
                bucket_service.upload_file(
                    object_name     = f"{base_path}/{file_name}_trg_pii.srt",
                    put_object_body = data,
                    msg             = True
                )
            elif trg_type == "TXT":
                # Inicializa Anonymizer
                anonymizer = AnonymizerEngine()

                # Analiza el texto completo
                results = analyzer.analyze(
                    text=text,
                    entities=[
                        "PERSON",
                        "LOCATION",
                        "PHONE_NUMBER",
                        "EMAIL_ADDRESS",
                        "IDENTIFIER",
                        "NUMBER",
                    ],
                    language="es",
                )

                # Anonimiza el texto completo
                anonymized = anonymizer.anonymize(text=text, analyzer_results=results)

                # Resultado final
                data = anonymized.text

                # Extraer path y nombre de archivo
                base_path, file_name = object_name.rsplit("/", 1)
                file_name = file_name.rsplit(".", 1)[0]

                # Upload file to Bucket
                bucket_service.upload_file(
                    object_name     = f"{base_path}/{file_name}_trg_pii.txt",
                    put_object_body = data,
                    msg             = True
                )
            

            # Process file extraction
            file_trg_extraction = data
            msg = db_file_service.update_extraction(file_id, file_trg_extraction)
            component.get_toast(msg, ":material/database:")

            # Process Vector Store
            msg = db_doc_service.vector_store(file_id)
            component.get_toast(msg, ":material/database:")
            
            mg = f"[Analyzer Engine] Module executed successfully."
            return mg, data

        except Exception as e:
            component.get_error(f"[Error] Presidio-Anonymizer PII:\n{e}")
            return False