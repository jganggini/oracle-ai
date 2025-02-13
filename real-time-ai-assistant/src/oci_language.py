import os
import oci
from oci.config import from_file
from oci.ai_language import AIServiceLanguageClient
from oci.ai_language.models import TextDocument, BatchDetectLanguageSentimentsDetails
from oci.exceptions import ServiceError
from dotenv import load_dotenv

# Cargar variables de entorno desde un archivo .env
load_dotenv()

def create_language_client() -> AIServiceLanguageClient:
    """Creates and returns an OCI AI Language client."""
    config = from_file()
    return AIServiceLanguageClient(config)

def create_text_document(key_: str, data: str) -> TextDocument:
    """Creates and returns a TextDocument object for sentiment analysis."""
    return TextDocument(
        key=key_,
        text=data,
        language_code = os.getenv('CON_LAN_LANGUAGE_CODE')
    )

def sentiment_analysis(data: str, level: str, text_model_key: str) -> dict:
    """
    Performs sentiment analysis on the provided data using OCI AI Language service.
    
    :param data: Text to analyze.
    :param text_model_key: Unique key for the text document.
    :return: Dictionary with sentiment analysis results or error message.
    """
    client = create_language_client()
    text_document = create_text_document(key_=text_model_key, data=data)

    try:
        response = client.batch_detect_language_sentiments(
            batch_detect_language_sentiments_details=BatchDetectLanguageSentimentsDetails(documents=[text_document]),
            level=[level] # SENTENCE/ASPECT
        )
        return response.data
    except ServiceError as e:
        print(f"Service error: {e}")
        return {"error": str(e)}
    except Exception as e:
        print(f"Unexpected error: {e}")
        return {"error": str(e)}