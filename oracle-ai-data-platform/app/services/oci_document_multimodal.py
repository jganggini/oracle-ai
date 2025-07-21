import io
import os
import oci
import fitz
import base64
from PIL import Image
import streamlit as st
import shutil

from langchain_community.chat_models import ChatOCIGenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableSerializable
from langchain_core.output_parsers.string import StrOutputParser


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

load_dotenv()

# Initialize the service
db_agent_service = database.AgentService()

class DocumentMultimodalService:
        
    def __init__(self):
        """
        Initializes the ModuleService with a shared database connection instance.
        """
        
    @staticmethod
    def create(
            object_name,
            strategy,
            user_id,
            agent_id,
            file_id,
            username
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
        # Obtener la extensión del archivo
        file_extension = object_name.split(".")[-1].lower()

        # Definir la carpeta de salida
        output_directory = f"files/{username}"

        # Eliminar la carpeta si existe y crearla nuevamente
        if os.path.exists(output_directory):
            shutil.rmtree(output_directory)
        os.makedirs(output_directory, exist_ok=True)

        # Strategy
        if strategy == "Double":
            DocumentMultimodalService.doble_page(object_name, output_directory)
        elif strategy == "Single":
            DocumentMultimodalService.single_page(object_name, file_extension, output_directory)

        data = DocumentMultimodalService.get_extraction(user_id, agent_id, output_directory)

        # Construct paths for processed objects
        processed_object_md = f"{object_name.rsplit('.', 1)[0]}_trg.md"
        
        #
        bucket_service.upload_file(processed_object_md, data)
        
        # Process file extraction
        msg = file_service.update_extraction(file_id, data)
        component.get_toast(msg, ":material/database:")
        
        # Process Vector Store
        msg = doc_service.vector_store(file_id)
        component.get_toast(msg, ":material/database:")
        
        mg = f"[AI Document Multimodal] Module executed successfully."
        return mg, data

    def single_page(object_name, file_extension, output_directory, msg: bool = False):
        """
        Procesa un archivo PDF o una imagen y guarda las páginas o imágenes en formato JPEG en una carpeta específica.

        Args:
            object_name (str): Nombre del archivo en el bucket.
            username (str): Nombre del usuario para crear una carpeta específica.
            msg (bool): Si se debe mostrar un mensaje de éxito o no.

        Returns:
            None
        """
        #try:
        # Procesar archivos basados en su extensión
        
        if file_extension == "pdf":
            # Obtener el archivo PDF desde el bucket
            object = bucket_service.get_object(object_name)
            if object:
                # Abrir el documento PDF desde el stream binario
                pdf_document = fitz.open(stream=object, filetype="pdf")

                # Iterar sobre cada página del documento
                for page_num in range(len(pdf_document)):
                    # Cargar la página actual
                    page = pdf_document[page_num]

                    # Convertir la página a un objeto pixmap
                    pix = page.get_pixmap(dpi=300, colorspace="rgb")

                    # Convertir el pixmap a un objeto PIL.Image
                    image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

                    # Guardar la imagen en formato JPEG
                    image_path = os.path.join(output_directory, f"doc_{page_num + 1}.jpeg")
                    image.save(image_path, format="JPEG", quality=95, optimize=True, progressive=True)

                # Cerrar el documento PDF
                pdf_document.close()
        

        elif file_extension in ["png", "jpeg", "jpg"]:
            # Guardar la imagen directamente
            object = bucket_service.get_object(object_name)
            if object:
                # Obtener el archivo PDF desde el bucket
                image = Image.open(io.BytesIO(object))
                if image.mode == 'RGBA':
                    image = image.convert('RGB')
                image_path = os.path.join(output_directory, f"img_1.jpeg")
                image.save(image_path, format="JPEG", quality=95, optimize=True, progressive=True)

        # Mostrar mensaje de éxito si se solicita
        if msg:
            component.get_toast("The file was processed successfully.", ":material/description:")
            

    def doble_page(object_name, output_directory, msg: bool = False):
        """
        Combina las páginas de un archivo PDF en pares, generando imágenes combinadas.
        Si el PDF tiene una sola página, se procesa como una única imagen.

        Args:
            object_name (str): Nombre del objeto PDF en el bucket.
            msg (bool): Si se debe mostrar un mensaje de éxito o no.

        Returns:
            list: Una lista de imágenes combinadas (o únicas) en formato base64.
        """
        data = []

        # Obtener el archivo PDF desde el bucket
        object = bucket_service.get_object(object_name)
        if object:
            # Abrir el documento PDF desde el stream binario
            pdf_document = fitz.open(stream=object, filetype="pdf")

            # Caso especial: si el PDF tiene solo una página
            if len(pdf_document) == 1:
                page = pdf_document[0]
                pix = page.get_pixmap(dpi=300, colorspace="rgb") 
                image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

                # Guardar la imagen en un buffer
                buffer = io.BytesIO()
                image.save(buffer, format="JPEG", quality=95, optimize=True, progressive=True)
                buffer.seek(0)

                # Codificar la imagen en base64
                encoded_image = base64.b64encode(buffer.read()).decode("utf-8")
                data.append(encoded_image)

            else:
                # Iterar sobre las páginas del documento en pares
                page_num = 0
                while page_num < len(pdf_document) - 1:
                    # Cargar las dos páginas actuales
                    page1 = pdf_document[page_num]
                    page2 = pdf_document[page_num + 1]

                    # Convertir las páginas a imágenes
                    pix1 = page1.get_pixmap(dpi=300)
                    pix2 = page2.get_pixmap(dpi=300)

                    # Convertir pixmaps a objetos PIL.Image
                    image1 = Image.frombytes("RGB", [pix1.width, pix1.height], pix1.samples)
                    image2 = Image.frombytes("RGB", [pix2.width, pix2.height], pix2.samples)

                    # Calcular el tamaño de la imagen combinada
                    combined_width = max(image1.width, image2.width)
                    combined_height = image1.height + image2.height

                    # Crear una nueva imagen combinada
                    combined_image = Image.new("RGB", (combined_width, combined_height))

                    # Pegar las dos imágenes en la imagen combinada
                    combined_image.paste(image1, (0, 0))
                    combined_image.paste(image2, (0, image1.height))

                    # Guardar la imagen en formato JPEG
                    image_path = os.path.join(output_directory, f"doc_{page_num + 1}.jpeg")
                    combined_image.save(image_path, format="JPEG", quality=95, optimize=True, progressive=True)

                    # Avanzar al siguiente par de páginas
                    page_num += 2

            # Cerrar el documento PDF
            pdf_document.close()

        # Mostrar mensaje de éxito si se solicita
        if msg:
            component.get_toast("The PDF was processed successfully.", ":material/description:")

        return data

    @staticmethod
    def get_extraction(user_id, agent_id, output_directory):
        # Filter modules by user and conditions
        df_agents = df_agents = db_agent_service.get_all_agents_cache(user_id, force_update=True)[lambda df: (df["AGENT_ID"].isin([agent_id]))]
        
        # Initialize the LLM model with configuration from the selected agent
        llm = ChatOCIGenAI(
            model_id         = str(df_agents["AGENT_MODEL_NAME"].values[0]),
            service_endpoint = os.getenv("CON_GEN_AI_SERVICE_ENDPOINT"),
            compartment_id   = os.getenv("CON_COMPARTMENT_ID"),
            provider         = str(df_agents["AGENT_MODEL_PROVIDER"].values[0]),
            is_stream        = False,
            auth_type        = os.getenv("CON_GEN_AI_AUTH_TYPE"),
            model_kwargs = {
                "max_tokens"        : int(df_agents["AGENT_MAX_OUT_TOKENS"].values[0]),
                "temperature"       : float(df_agents["AGENT_TEMPERATURE"].values[0]),
                "top_p"             : float(df_agents["AGENT_TOP_P"].values[0]),
                "top_k"             : int(df_agents["AGENT_TOP_K"].values[0]),
                "frequency_penalty" : float(df_agents["AGENT_FREQUENCY_PENALTY"].values[0]),
                "presence_penalty"  : float(df_agents["AGENT_PRESENCE_PENALTY"].values[0])
            }
        )

        #
        prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", str(df_agents["AGENT_PROMPT_SYSTEM"].values[0])),
                ("user",
                    [
                        {
                            "type": "image_url",
                            "image_url": {"url": "data:image/jpeg;base64,{input_imagen}"},
                            "detail": "high",
                        }
                    ]
                ),
            ]
        )
        
        #
        chain = prompt_template | llm | StrOutputParser()

        #
        base64_images = utl_function_service.encode_images_to_base64(output_directory)

        result = chain.batch(
            [{"input_imagen": input_imagen} for input_imagen in base64_images],
            max_concurrency=2
        )

        # Combine Markdown content from all pages
        markdown_output = "".join(result)
        
        return markdown_output