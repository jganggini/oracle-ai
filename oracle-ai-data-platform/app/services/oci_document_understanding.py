import os
import oci
import uuid
import fitz

from dotenv import load_dotenv
import components as component
import services as service
import services.database as database
import utils as utils

# Initialize services
config               = oci.config.from_file(profile_name=os.getenv('CON_OCI_PROFILE_NAME', 'DEFAULT'))
bucket_service       = service.BucketService()
file_service         = database.FileService()
doc_service          = database.DocService()
utl_function_service = utils.FunctionService()
language_map         = {
    "Spanish"    : "es",
    "Portuguese" : "pt",
    "English"    : "en"
}

load_dotenv()

class DocumentUnderstandingService:

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
            object_location = oci.ai_document.models.ObjectLocation(
                namespace_name = os.getenv('CON_ADB_BUK_NAMESPACENAME'),
                bucket_name    = os.getenv('CON_ADB_BUK_NAME'),
                object_name    = object_name
            )
            output_location = oci.ai_document.models.OutputLocation(
                namespace_name = os.getenv('CON_ADB_BUK_NAMESPACENAME'),
                bucket_name    = os.getenv('CON_ADB_BUK_NAME'),
                prefix         = prefix
            )

            # Configure processor job details
            processor_job_details = oci.ai_document.models.CreateProcessorJobDetails(
                display_name     = str(uuid.uuid4()),
                compartment_id   = os.getenv('CON_COMPARTMENT_ID'),
                input_location   = oci.ai_document.models.ObjectStorageLocations(object_locations=[object_location]),
                output_location  = output_location,
                processor_config = oci.ai_document.models.GeneralProcessorConfig(
                    features =[
                        oci.ai_document.models.DocumentTextExtractionFeature(generate_searchable_pdf=True),
                        #oci.ai_document.models.DocumentTableExtractionFeature(),
                        #oci.ai_document.models.DocumentKeyValueExtractionFeature(),
                        #oci.ai_document.models.DocumentLanguageClassificationFeature(),
                    ],
                    language = language
                )
            )

            # Create the processor job and wait for completion
            aiservicedocument_client = oci.ai_document.AIServiceDocumentClientCompositeOperations(
                oci.ai_document.AIServiceDocumentClient(config)
            )
            response = aiservicedocument_client.create_processor_job_and_wait_for_state(
                create_processor_job_details=processor_job_details,
                wait_for_states=[oci.ai_document.models.ProcessorJob.LIFECYCLE_STATE_SUCCEEDED]
            )
            processor_job = response.data
        
            if processor_job:

                # Construct paths for processed objects
                processed_object_base = f"{prefix}/{processor_job.id}"
                processed_object_pdf  = f"{processed_object_base}/{output_location.namespace_name}_{output_location.bucket_name}/searchablePdf/{object_name}.pdf"
                processed_object_json = f"{processed_object_base}/{output_location.namespace_name}_{output_location.bucket_name}/results/{object_name}.json"

                # Extract base path and filename without extension
                base_path, file_name = object_name.rsplit("/", 1)
                file_name = file_name.rsplit(".", 1)[0]

                # Move PDF file
                object_name_pdf = f"{base_path}/{file_name}_trg.pdf"                
                bucket_service.move_object(processed_object_pdf, object_name_pdf)

                # Move JSON file
                object_name_json = f"{base_path}/{file_name}_trg.json"
                bucket_service.move_object(processed_object_json, object_name_json)

                # List and delete all objects in the processed folder
                list_objects = bucket_service.list_objects(processed_object_base)
                for obj_name in list_objects:
                    bucket_service.delete_object(obj_name)

                # Build the new name for the processed file
                object_name_trg = f"{object_name.rsplit('.', 1)[0]}_trg.pdf"
                
                # Process the PDF and extract data
                data = DocumentUnderstandingService.process_pdf(object_name_trg)
                
                # Process file extraction
                file_trg_extraction = "\n".join([str(page["content"]) for page in data if "content" in page]) if data else ""
                msg = file_service.update_extraction(file_id, file_trg_extraction)
                component.get_toast(msg, ":material/database:")
                
                # Process Vector Store
                msg = doc_service.vector_store(file_id)
                component.get_toast(msg, ":material/database:")
                
                mg = f"[AI Document Understanding] Module executed successfully."
                return mg, data

        except Exception as e:
            component.get_error(f"[Error] Creating Document Understanding:\n{e}")
        
    @staticmethod
    def process_pdf(object_name, msg: bool = False):
        """
        Processes a PDF file from the OCI bucket and extracts text from each page.

        Args:
            object_name (str): Name of the PDF object in the bucket.

        Returns:
            list: A list of dictionaries, where each dictionary contains:
                - "page_number": The page number (1-based index).
                - "content": The extracted text from the page.
                - "characters": The character count of the page.
        """
        try:
            # List to store the extracted data
            data = []

            # Retrieve the PDF stream from the bucket
            object = bucket_service.get_object(object_name)
            if object:
                # Open the PDF document from the binary stream
                pdf_document = fitz.open(stream=object, filetype='pdf')

                # Iterate over each page in the PDF document
                for page_num in range(len(pdf_document)):
                    # Load the current page
                    page = pdf_document.load_page(page_num)

                    # Extract text content from the page
                    content = page.get_text("text")

                    # Append the extracted text and page number to the data list
                    data.append({
                        "content"     : content.strip(),     # Strip any extra whitespace
                        "page_number" : page_num + 1,        # Convert 0-based index to 1-based index
                        "characters"  : len(content.strip()) # Characters
                    })

            component.get_toast(f"The PDF was processed successfully.", ":material/description:") if msg else None
            return data

        except Exception as e:
            component.get_error(f"[Error] Processing PDF:\n{e}")
            return []