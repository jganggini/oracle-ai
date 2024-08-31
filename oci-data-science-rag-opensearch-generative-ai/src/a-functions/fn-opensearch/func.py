import io
import json
import oci
import requests
import uuid
import logging
import fitz # PyMuPDF

from pathlib import Path

from spire.doc import Document
from spire.doc import FileFormat as DocFileFormat
from spire.xls import Workbook
from spire.xls.common import Encoding

import pytest
from fdk import fixtures
from fdk import response

################################
#           Parameter          #
################################
root        = str(Path(__file__).parent.absolute())
#oci
profile     = 'LOCAL' # OCI: The profile parameter (profile) 'LOCAL' or 'FUNCTION' in OCI
config      = oci.config.from_file(root + "/oci/config", profile)
client      = oci.object_storage.ObjectStorageClient(config)
namespace   = client.get_namespace().data
prefix      = "ocr"
tmp         = "/tmp"

# Opensearch
apiEndpoint = "http://***.***.***.***:9200"
username    = "opensearch"
password    = "**********"
searchIndex = "oci_documents"

################################
#    Controlador de Eventos    #
################################
# Function to handle incoming events and process documents
def handler(ctx, data: io.BytesIO = None):  
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    var_data = data.getvalue()
    
    try:
        if var_data.decode(encoding='utf-8') != '':
            body = json.loads(var_data)

            # Extract metadata 
            bucketName = body["data"]["additionalDetails"]["bucketName"]
            objectName = body["data"]["resourceName"]

            # Opensearch > Mappings
            obj_name = objectName
            obj_type = Path(objectName).suffix[1:].lower()  # Extract file extension
            obj_url = f"https://objectstorage.us-chicago-1.oraclecloud.com/n/{namespace}/b/{bucketName}/o/{objectName}"
            
            # Process the content based on file type
            openSearchData = ""
            resp = {}  # Resultado de la inserción
            if (obj_type in ["jpg", "png", "pdf", "tiff"]) and (prefix not in obj_url):
                # Get the object data from Object Storage
                obj_content = get_object(bucketName, objectName)
                # Sent to OCI Document Understanding (JPG, PNG, PDF, and TIFF files are supported)
                obj_content_ocr = send_to_document_understanding(bucketName, obj_content, obj_name)
                openSearchData = process_pdf(obj_content_ocr, obj_name, obj_type, obj_url)
                # Insert into OpenSearch
                resp = opensearch_insert(openSearchData)
            elif obj_type in ["docx", "doc"]:
                obj_content = get_object(bucketName, objectName)
                obj_bytes = convert_docx_to_pdf(obj_content, obj_name)
                openSearchData = process_pdf(obj_bytes, obj_name, obj_type, obj_url)
                resp = opensearch_insert(openSearchData)
            elif obj_type in ["xlsx", "xls"]:
                obj_content = get_object(bucketName, objectName)
                obj_bytes = convert_xlsx_to_pdf(obj_content, obj_name)
                openSearchData = process_pdf(obj_bytes, obj_name, obj_type, obj_url)
                resp = opensearch_insert(openSearchData)
            
            if "items" in resp:
                logger.info(f"[opensearch_insert] The document data was inserted correctly (Success)")
                logger.info("---[END]---")
            else:
                logger.warn(f"[opensearch_insert] Unsupported Format: {objectName}")
        else:
            logger.error("[handler] No Message.")
    except (Exception, ValueError) as e:
        logger.error(str(e))
        raise

# Function to get an object from OCI Object Storage
def get_object(bucketName, objectName):
    logger = logging.getLogger()
    
    logger.info("---[INI]---")
    logger.info(f"[handler] Function invoked for Objcet Create in Bucket: {bucketName}")
    
    try:    
        logger.info(f"[get_object] Searching for Bucket and Object...")
        
        # Retrieve the object from OCI Object Storage
        object = client.get_object(namespace, bucketName, objectName)
        # Extract the file name from the object name
        file_name = Path(objectName).name
        
        if object.status == 200:
            logger.info(f"[get_object] Found Object {'ocr/../' + file_name if '.pdf.pdf' in file_name else file_name} (Success)")
        else:
            raise Exception(f"[get_object] Not Found Object {'ocr/../' + file_name if '.pdf.pdf' in file_name else file_name} (Failed)")
    except Exception as e:
        logger.error(f"[get_object] {str(e)}.")

    return object.data.content

# Function to insert data into OpenSearch
def opensearch_insert(openSearchData):
    logger = logging.getLogger()
    
    # Request Format
    bulkinserturl = f"{apiEndpoint}/{searchIndex}/_bulk?refresh=wait_for"
    auth          = (username, password)
    headers       = {"Content-Type": "application/x-ndjson"}

    try:
        resp = requests.post(bulkinserturl, auth=auth, headers=headers, data=openSearchData)
        resp.raise_for_status()
        return resp.json()
        
    except requests.exceptions.RequestException as e:
        logger.error(f"[opensearch_insert] {str(e)}.")
        raise

# Function to format data for OpenSearch insertion
def format_opensearch_data(obj_name, content, page_num, obj_type, obj_url):
    action   = json.dumps({"index": {}})
    document = json.dumps({"obj_content": content,
                           "obj_name": obj_name,
                           "obj_page": page_num,
                           "obj_type": obj_type,
                           "obj_url": obj_url})
    return f"{action}\n{document}\n"

# Function to process PDF content and prepare it for OpenSearch
def process_pdf(obj, obj_name, obj_type, obj_url):
    logger = logging.getLogger()
    
    openSearchData = ""
    pdf_document = fitz.open(stream=obj, filetype='pdf')
    
    try:
        # Iterate over each page in the PDF document
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num) # Load the current page
            content = page.get_text("text") # Extract text content from the page
            # Format the extracted text content for OpenSearch and append it to openSearchData
            openSearchData += format_opensearch_data(obj_name, content, page_num + 1, obj_type, obj_url)
        
        logger.info(f"[process_pdf] Convert PDF format to OpenSearch Index (Success)")

        return openSearchData

    except Exception as e:
        logger.error(f"[process_pdf] {str(e)}.")
        raise

# Function to convert DOCX to PDF
def convert_docx_to_pdf(docx_bytes, obj_name):
    logger = logging.getLogger()
    
    try:
        with open(f"{tmp}/{obj_name}.docx", 'wb') as f:
            f.write(docx_bytes)

        # Convert DOCX to PDF using Spire.Doc
        document = Document()
        document.LoadFromFile(f"{tmp}/{obj_name}.docx")
        document.SaveToFile(f"{tmp}/{obj_name}.pdf", DocFileFormat.PDF)
        document.Close()

        with open(f"{tmp}/{obj_name}.pdf", 'rb') as f:
            pdf_bytes = f.read()

        # Clean up temporary files
        Path(f"{tmp}/{obj_name}.docx").unlink()
        Path(f"{tmp}/{obj_name}.pdf").unlink()

        logger.info(f"[convert_docx_to_pdf] Convert DOCX format to PDF (Success)")

        return pdf_bytes

    except Exception as e:
        logger.error(f"[convert_docx_to_pdf] {str(e)}.")
        raise

# Function to convert XLSX to PDF
def convert_xlsx_to_pdf(xlsx_bytes, obj_name):
    logger = logging.getLogger()
    
    try:
        with open(f"{tmp}/{obj_name}.xlsx", "wb") as f:
            f.write(xlsx_bytes)

        # Create a Workbook object
        workbook = Workbook()

        # Load an Excel document
        workbook.LoadFromFile(f"{tmp}/{obj_name}.xlsx")

        # Iterate through the worksheets in the workbook
        for sheet in workbook.Worksheets:
            sheet.SaveToFile(f"{tmp}/{obj_name}.txt", '  ', Encoding.get_UTF8())

        # Convert TXT to PDF using Spire.Doc
        document = Document()
        document.LoadFromFile(f"{tmp}/{obj_name}.txt")
        document.SaveToFile(f"{tmp}/{obj_name}.pdf", DocFileFormat.PDF)
        document.Close()

        with open(f"{tmp}/{obj_name}.pdf", "rb") as f:
            pdf_bytes = f.read()

        # Clean up temporary files
        Path(f"{tmp}/{obj_name}.xlsx").unlink()
        Path(f"{tmp}/{obj_name}.txt").unlink()
        Path(f"{tmp}/{obj_name}.pdf").unlink()
    
        logger.info(f"[convert_xlsx_to_pdf] Convert XLSX format to PDF (Success)")

        return pdf_bytes

    except Exception as e:
        logger.error(f"[convert_xlsx_to_pdf] {str(e)}.")
        raise

# Function to send the PDF to OCI Document Understanding
def send_to_document_understanding(bucketName, obj_content, obj_name):
    logger = logging.getLogger()
    
    try:
        # Setup input location where document being processed is stored.
        object_location = oci.ai_document.models.ObjectLocation()
        object_location.namespace_name = namespace
        object_location.bucket_name    = bucketName
        object_location.object_name    = obj_name

        # Setup the output location where processor job results will be created
        output_location = oci.ai_document.models.OutputLocation()
        output_location.namespace_name = namespace
        output_location.bucket_name    = bucketName
        output_location.prefix         = prefix

        # Text extraction feature
        text_extraction_feature = oci.ai_document.models.DocumentTextExtractionFeature(
            generate_searchable_pdf = True  # Enable PDF Generation
        )

        # Create the details for the processor job with text extraction feature
        create_processor_job_details_text_extraction = oci.ai_document.models.CreateProcessorJobDetails(
            display_name     = str(uuid.uuid4()),
            compartment_id   = config["compartment_id"],
            input_location   = oci.ai_document.models.ObjectStorageLocations(object_locations=[object_location]),
            output_location  = output_location,
            processor_config = oci.ai_document.models.GeneralProcessorConfig(features=[text_extraction_feature], language="SPA")
        )
        
        # Create an instance of AIServiceDocumentClientCompositeOperations using AIServiceDocumentClient with the given configuration
        aiservicedocument_client = oci.ai_document.AIServiceDocumentClientCompositeOperations(oci.ai_document.AIServiceDocumentClient(config))

        # Create the processor job and wait for it to reach the 'SUCCEEDED' state
        create_processor_response = aiservicedocument_client.create_processor_job_and_wait_for_state(
            create_processor_job_details = create_processor_job_details_text_extraction,
            wait_for_states              = [oci.ai_document.models.ProcessorJob.LIFECYCLE_STATE_SUCCEEDED]
        )

        processor_job = create_processor_response.data

        logger.info(f"[send_to_document_understanding] OCR process completed (Success)")

        objectName = f"{output_location.prefix}/{processor_job.id}/{output_location.namespace_name}_{output_location.bucket_name}/searchablePdf/{obj_name}.pdf"
        obj_content = get_object(bucketName, objectName)
        
        return obj_content

    except Exception as e:
        logger.error(f"[send_to_document_understanding] {str(e)}")
        raise


################################
#            PyTest            #
################################
@pytest.mark.asyncio
async def test_parse_request_with_data():
    print("@pytest")
    # Produce Test Message
    with open("test_event_pdf.json", "rb") as fh:
        data = io.BytesIO(fh.read())
    
    call = await fixtures.setup_fn_call(handler, content=data)

    content, status, headers = await call

    assert 200 == status
    # python3 -m venv env-opensearch
    # source env-opensearch/bin/activate
    # pip install --upgrade -r requirements.txt
    # python -m pytest -v -s --tb=long func.py
    # fn -v deploy --app app-demo
    # fn invoke app-demo fn-opensearch