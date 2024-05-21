
[![Issues][issues-shield]][issues-url]
[![LinkedIn][linkedin-shield]][linkedin-url]


<!-- PROJECT LOGO -->
<br />
<p align="center">

  <h2 align="center">OCI Data Science + Vision AI</h3>

  <p align="center">
    Detección de Objetos en Video
    <br />
    <a href="./src"><strong>Explore the code »</strong></a>
    <br />
    <br />
    <a href="https://youtube.com/@jganggini">🎬 View Demo</a>
    ·
    <a href="https://github.com/jganggini/oracle-ai/issues">Report Bug</a>
    ·
    <a href="https://github.com/jganggini/oracle-ai/pulls">Request Feature</a>
  </p>
</p>

## Introducción

Este notebook demuestra cómo usar los servicios de Oracle Cloud Infrastructure (OCI) para detectar objetos en videos utilizando servicios de Visión AI y Ciencia de Datos. Incluye pasos para configurar el entorno, autenticarse con OCI y ejecutar la detección de objetos en archivos de video.

## Prerrequisitos

Antes de ejecutar el notebook, asegúrate de tener lo siguiente:

- Una cuenta de Oracle Cloud con acceso a los servicios de Ciencia de Datos y Almacenamiento de Objetos.
- Python instalado en tu máquina local o un entorno conda configurado.
- Las siguientes bibliotecas de Python instaladas:
  - `oci`
  - `ads`
  - `opencv-python`
  - `tqdm`
  - `jupyterlab-widgets`

Puedes instalar las bibliotecas requeridas usando los siguientes comandos:
```bash
pip install oci
pip install ads
pip install opencv-python
pip install tqdm
pip install jupyterlab-widgets
```

## Estructura del Notebook

### Paso 1: Bibliotecas y Autenticación

En esta sección, importamos las bibliotecas necesarias y configuramos la autenticación utilizando el recurso principal de OCI.

#### Instalación de Bibliotecas

- `oci`: Biblioteca para interactuar con los servicios de Oracle Cloud Infrastructure.
- `ads`: Biblioteca de Oracle para facilitar las tareas de ciencia de datos en OCI.
- `opencv-python`: Biblioteca para procesamiento de imágenes y videos.
- `tqdm`: Biblioteca para mostrar barras de progreso en bucles.
- `jupyterlab-widgets`: Biblioteca para agregar widgets interactivos en Jupyter Notebooks.

### Paso 2: Cliente de Almacenamiento de Objetos

Creamos el cliente de Almacenamiento de Objetos usando el firmante de ADS para acceder y manipular datos en el Almacenamiento de Objetos de OCI.

### Paso 3: Funciones

Esta sección incluye funciones utilizadas a lo largo del notebook.

#### Función: `fn_get_object`

Recupera un objeto del bucket especificado en el Almacenamiento de Objetos de OCI.

**Parámetros:**
- `namespace` (str): El espacio de nombres del Almacenamiento de Objetos.
- `bucket_name` (str): El nombre del bucket del cual recuperar el objeto.
- `object_name` (str): El nombre del objeto a recuperar.

**Devuelve:**
- `oci.object_storage.models.ObjectSummary`: El objeto recuperado del bucket especificado.

#### Función: `fn_download`

Descarga el contenido de un objeto y lo guarda en una ruta local.

**Parámetros:**
- `object_content` (oci.object_storage.models.ObjectSummary): El contenido del objeto a descargar.
- `local_video_path` (str): La ruta local donde se guardará el video.

#### Función: `fn_clean_folder`

Limpia todos los archivos en una carpeta especificada.

**Parámetros:**
- `folder_path` (str): La ruta de la carpeta de la cual eliminar todos los archivos.

#### Función: `fn_create_or_clean_folder`

Crea una carpeta nueva o limpia su contenido si ya existe.

**Parámetros:**
- `folder_path` (str): La ruta de la carpeta a crear o limpiar.

#### Función: `save_frame`

Guarda un fotograma específico de un video en una carpeta de salida.

**Parámetros:**
- `video_path` (str): La ruta del archivo de video de entrada.
- `output_folder` (str): La carpeta de salida donde se guardarán los fotogramas.
- `frame_number` (int): El número de fotograma a guardar.
- `fps_rate` (float): La tasa de fotogramas por segundo del video.

#### Función: `fn_extract_images_from_parallel_video`

Extrae imágenes de un video en paralelo utilizando múltiples hilos.

**Parámetros:**
- `video_path` (str): La ruta del archivo de video de entrada.
- `output_folder` (str): La carpeta de salida donde se guardarán los fotogramas.
- `max_workers` (int): El número máximo de hilos a usar.
- `fps_rate` (float, opcional): La tasa de fotogramas por segundo del video.

#### Función: `fn_seconds_to_hms`

Convierte segundos en una cadena de texto con formato horas, minutos y segundos.

**Parámetros:**
- `seconds` (int): El número de segundos a convertir.

**Devuelve:**
- `str`: La cadena de texto con el formato `HH:MM:SS`.

#### Función: `fn_get_object_detection_vision`

Realiza la detección de objetos en una imagen utilizando el servicio Vision AI de OCI.

**Parámetros:**
- `image_path` (str): La ruta de la imagen a analizar.
- `compartment_id` (str): El ID del compartimento de OCI.
- `model_id` (str): El ID del modelo de detección de objetos.

**Devuelve:**
- `oci.ai_vision.models.DetectLanguageResponse`: La respuesta del servicio Vision AI.

#### Función: `fn_process_all_images_parallel_vision`

Procesa todas las imágenes en una carpeta en paralelo utilizando múltiples hilos y el servicio Vision AI de OCI.

**Parámetros:**
- `folder_path` (str): La carpeta que contiene las imágenes a procesar.
- `compartment_id` (str): El ID del compartimento de OCI.
- `model_id` (str): El ID del modelo de detección de objetos.
- `max_workers` (int): El número máximo de hilos a usar.

#### Función: `fn_get_duration`

Obtiene la duración de un video.

**Parámetros:**
- `video_path` (str): La ruta del archivo de video.

**Devuelve:**
- `float`: La duración del video en segundos.

#### Función: `fn_get_result`

Genera resultados de detección de objetos y los guarda en un archivo local.

**Parámetros:**
- `df_results` (pd.DataFrame): DataFrame con los resultados de detección de objetos.
- `local_video_path` (str): La ruta local del video procesado.

#### Función: `fn_get_time_segments`

Obtiene los segmentos de tiempo de las detecciones de objetos.

**Parámetros:**
- `df_results` (pd.DataFrame): DataFrame con los resultados de detección de objetos.

**Devuelve:**
- `list`: Lista de segmentos de tiempo.

#### Función: `fn_get_image_base64`

Convierte una imagen a una cadena base64.

**Parámetros:**
- `path` (str): La ruta de la imagen.

**Devuelve:**
- `str`: La cadena base64 de la imagen.

#### Función: `fn_image_formatter`

Formatea una imagen para su visualización en HTML.

**Parámetros:**
- `path` (str): La ruta de la imagen.

**Devuelve:**
- `str`: La cadena HTML para mostrar la imagen.

#### Función: `fn_get_result_list`

Obtiene una lista de resultados de detección de objetos.

**Parámetros:**
- `df_results` (pd.DataFrame): DataFrame con los resultados de detección de objetos.

**Devuelve:**
- `list`: Lista de resultados de detección de objetos.

### Pasos y Funciones Adicionales

El notebook continúa con pasos y funciones adicionales para procesar archivos de video, detectar objetos y visualizar los resultados. Cada función y bloque de código se explica con comentarios detallados dentro del propio notebook.

## Ejecutar el Notebook

1. Asegúrate de tener todos los prerrequisitos instalados.
2. Abre el notebook en JupyterLab o Jupyter Notebook.
3. Sigue los pasos secuencialmente, ejecutando cada celda para configurar el entorno, autenticarte y ejecutar el proceso de detección de objetos.


<!-- Contacto -->
## Contacto
Project Link: [https://github.com/jganggini](https://github.com/jganggini)

<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[issues-shield]: https://img.shields.io/github/issues/othneildrew/Best-README-Template.svg?style=for-the-badge
[issues-url]: https://github.com/jganggini/oci-functions/issues
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: https://www.linkedin.com/in/jganggini/