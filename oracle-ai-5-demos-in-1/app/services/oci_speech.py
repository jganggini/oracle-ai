import os
import oci
import uuid
import json
import time

from dotenv import load_dotenv
import components as component
import services as service
import services.database as database
import utils as utils

# Initialize services
config               = oci.config.from_file(profile_name=os.getenv('CON_PROFILE_NAME'))
bucket_service       = service.BucketService()
db_file_service      = database.FileService()
db_doc_service       = database.DocService()
utl_function_service = utils.FunctionService()
language_map         = {
    "Spanish"    : "es",
    "Portuguese" : "pt",
    "English"    : "en"
}

load_dotenv()

class SpeechService:

    @staticmethod
    def create(
            object_name,
            prefix,
            language,
            file_id
        ):
        """
        Sends a document to the OCI Document Understanding service for processing.

        Args:
            object_name (str) : The name of the object in the OCI bucket.
            prefix (str)      : The output prefix for processed files.
            language (str)    : The language of the document (e.g., 'English', 'Spanish').
            file_id (str)     : The ID of the file to associate with the vector store.

        Returns:
            tuple: A success message and extracted data, or an error message.
        """
        try:
             # Map language to code
            language = language_map.get(language)

            # Configure input and output locations
            object_location = oci.ai_speech.models.ObjectLocation(
                namespace_name = os.getenv('CON_ADB_BUK_NAMESPACENAME'),
                bucket_name    = os.getenv('CON_ADB_BUK_NAME'),
                object_names   = [object_name]
            )
            input_location = oci.ai_speech.models.ObjectListInlineInputLocation(
                location_type    = "OBJECT_LIST_INLINE_INPUT_LOCATION",
                object_locations = [object_location],
            )
            output_location = oci.ai_speech.models.OutputLocation(
                namespace_name = os.getenv('CON_ADB_BUK_NAMESPACENAME'),
                bucket_name    = os.getenv('CON_ADB_BUK_NAME'),
                prefix         = prefix
            )
            normalization = oci.ai_speech.models.TranscriptionNormalization(
                is_punctuation_enabled = True
            )
            diarization = oci.ai_speech.models.Diarization(
                is_diarization_enabled = True,
                number_of_speakers     = 2,
            )
            transcription_settings = oci.ai_speech.models.TranscriptionSettings(
                diarization = diarization
            )
            model_details = oci.ai_speech.models.TranscriptionModelDetails(
                language_code = language,
                model_type    = "WHISPER_MEDIUM",
                transcription_settings = transcription_settings,
            )
            
            # Configure processor job details
            transcription_job_details = oci.ai_speech.models.CreateTranscriptionJobDetails(
                display_name    = str(uuid.uuid4()),
                compartment_id  = os.getenv('CON_COMPARTMENT_ID'),
                description     = "App",
                model_details   = model_details,
                input_location  = input_location,
                additional_transcription_formats=["SRT"],
                normalization   = normalization,
                output_location = output_location
            )

            # Create the processor job and wait for completion
            aiservicespeech_client = oci.ai_speech.AIServiceSpeechClient(config)
            response = aiservicespeech_client.create_transcription_job(
                create_transcription_job_details=transcription_job_details
            )
            transcription_job = response.data

            if transcription_job:
                
                while True:
                    get_transcription_job_response = aiservicespeech_client.get_transcription_job(
                        transcription_job_id = transcription_job.id)
                    
                    if get_transcription_job_response.data.lifecycle_state == "SUCCEEDED":
                        break
                    time.sleep(5)
                
                # Construct paths for processed objects                
                transcription_object_base = transcription_job.output_location.prefix[:-1]
                #object_name = transcription_job.input_location.object_locations.object_names

                transcription_object_json  = f"{transcription_object_base}/{output_location.namespace_name}_{output_location.bucket_name}_{object_name}.json"
                transcription_object_srt = f"{transcription_object_base}/{output_location.namespace_name}_{output_location.bucket_name}_{object_name}.srt"
                
                # Extract base path and filename without extension
                base_path, file_name = object_name.rsplit("/", 1)
                file_name = file_name.rsplit(".", 1)[0]

                # Move JSON file
                object_name_json = f"{base_path}/{file_name}_trg.json"
                bucket_service.move_object(transcription_object_json, object_name_json)
                
                # Move SRT file
                object_name_srt = f"{base_path}/{file_name}_trg.srt"
                bucket_service.move_object(transcription_object_srt, object_name_srt)

                # List and delete all objects in the processed folder
                list_objects = bucket_service.list_objects(transcription_object_base)
                for obj_name in list_objects:
                    bucket_service.delete_object(obj_name)

                # Build the new name for the processed file
                object_name_trg = f"{object_name.rsplit('.', 1)[0]}_trg.srt"
                
                # Process the PDF and extract data
                data = SpeechService.process_srt(object_name_trg)
                
                # Process file extraction
                file_trg_extraction = str(data)
                msg = db_file_service.update_extraction(file_id, file_trg_extraction)
                component.get_toast(msg, ":material/database:")
                
                # Process Vector Store
                msg = db_doc_service.vector_store(file_id)
                component.get_toast(msg, ":material/database:")
                
                mg = f"[AI Speech] Module executed successfully."
                return mg, data

        except Exception as e:
            component.get_error(f"[Error] Creating Speech:\n{e}")

    @staticmethod
    def process_srt(object_name, msg: bool = False):
        """
        Processes a SRT file from the OCI bucket and extracts its content.

        Args:
            object_name (str): Name of the SRT object in the bucket.
            msg (bool): If True, shows a toast message upon successful processing.

        Returns:
            dict: The parsed SRT content as a dictionary.
        """
        try:
            # List to store the extracted data
            data = []
            
            # Retrieve the JSON object from the bucket
            object = bucket_service.get_object(object_name)

            if object:
                # Decode bytes to string and parse SRT
                data = object.decode('utf-8')

            component.get_toast(f"The SRT was processed successfully.", ":material/description:") if msg else None
            return data

        except Exception as e:
            component.get_error(f"[Error] Processing SRT:\n{e}")
            return []