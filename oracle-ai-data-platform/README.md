[![Issues][issues-shield]][issues-url]
[![LinkedIn][linkedin-shield]][linkedin-url]


<!-- Intro -->
<br />
<div align="center" style="text-align:center;">
  <img align="center" src="img/smart_toy.svg" width="200" height="200"></img>
  <h1 style="font-size:40px; font-bload"><b style="color:#ec4b42">Oracle AI</b> Data Platform</h1>
  
  <a style="font-size:large;" href="/src/">👨🏽‍💻 Explore the Code »</a>
  <br/>
  <a href="https://www.youtube.com/watch?v=6L1YmTRZNxM&list=PLMUWTQHw13gbk738EGtr0fWwi40B81qEw">🎬 View Demo</a>
  ·
  <a href="https://github.com/jganggini/oci-functions/issues">💣 Report Bug</a>
  ·
  <a href="https://github.com/jganggini/oci-functions/pulls">🚀 Request Feature</a>
</div>

## Requisitos Previos

### 1. Cuenta en Oracle Cloud Infrastructure (OCI)
Si no tiene una cuenta, regístrese en [Oracle Cloud](https://www.oracle.com/cloud/).

✅ Recomendación: Para garantizar compatibilidad con todos los servicios requeridos, elige una región como `us-chicago-1`.

### 2. Servicios Necesarios

<div align="center" style="text-align:center;">
  <table align="center">
    <tr style="font-size:medium;">
      <td colspan="4">Oracle Cloud</td>
      <td colspan="4">AI Stack</td>
    </tr>
    <tr align="center" >
      <td><img src="img/oci-generative-ai.svg" width="50" height="50"></td>
      <td><img src="img/oci-autonomous-database.svg" width="50" height="50"></td>
      <td><img src="img/oci-document-understanding.svg" width="50" height="50"></td>
      <td><img src="img/oci-speech.svg" width="50" height="50"></td>
      <td><img src="img/nvidia.svg" width="50" height="50"></td>
      <td><img src="img/grok.svg" width="50" height="50"></td>
      <td><img src="img/meta.svg" width="50" height="50"></td>
      <td><img src="img/langchain.svg" width="50" height="50"></td>
      <td><img src="img/streamlit.svg" width="50" height="50"></td>
    </tr>
    <tr style="font-size:small;">
      <td>Generative AI</td>
      <td>Autonomous <br/> Database 23ai</td>
      <td>Document <br/> Undestanding</td>
      <td>Speech <br/> Realtime</td>
      <td>NVidia</td>
      <td>xAI Grok</td>
      <td>Meta</td>
      <td>LangChain</td>
      <td>Streamlit</td>
    </tr>
  </table>
</div>

#### a) Autonomous Database
- Despliegue una instancia de Autonomous Database en OCI.

#### b) Object Storage Bucket
- Cree un bucket en OCI Object Storage.

#### c) Configurar Políticas de IAM
Se deben configurar las siguientes políticas para permitir el acceso adecuado:

##### c.1) OCI Document Understanding
```plaintext
Allow any-user to manage ai-service-document-family in tenancy
```
Read more: [About Document Understanding Policies](https://docs.oracle.com/en-us/iaas/Content/document-understanding/using/about_document-understanding_policies.htm).

##### c.2) OCI Speech
```plaintext
Allow any-user to manage ai-service-speech-family in tenancy
Allow any-user to read tag-namespaces in tenancy
Allow any-user to inspect tag-namespaces in tenancy
```
Read more: [About Speech Policies](https://docs.oracle.com/en-us/iaas/Content/speech/using/policies.htm).

##### c.3) OCI Generative AI
```plaintext
Allow any-user to manage generative-ai-family in tenancy
```
Read more: [Getting Access to Generative AI](https://docs.oracle.com/en-us/iaas/Content/generative-ai/iam-policies.htm).

##### c.4) Bucket
```plaintext
Allow any-user to read buckets in tenancy
Allow any-user to manage object-family in tenancy
Allow any-user to read objectstorage-namespaces in tenancy
```

##### c.5) All Resources (Optional)
Si estás realizando pruebas o laboratorios en una cuenta trial de Oracle Cloud, puedes usar temporalmente la siguiente política para facilitar el acceso sin restricciones:

```plaintext
Allow any-user to manage all-resources in tenancy
```

Esta política otorga permisos completos a todos los usuarios autenticados sobre todos los recursos en el tenancy, por lo que debe utilizarse únicamente en entornos controlados, personales y no compartidos. Se recomienda eliminarla una vez finalizadas las pruebas para evitar acciones accidentales o un consumo innecesario de recursos que puedan agotar tu crédito trial.

### 3. Requisitos de la Máquina Local
- **Sistema Operativo:** Windows o macOS.
- **Anaconda (Conda):** Descargue e instale desde [Anaconda](https://www.anaconda.com/products/distribution).
- **Git:** Descargue e instale [Git](https://git-scm.com/).

## Instalación del Proyecto

### 1. Clonar el Repositorio
Ejecute en la terminal:
```bash
git clone https://github.com/jganggini/oracle-ai.git
```
O descargue el ZIP del repositorio y extraiga su contenido.

### 2. Crear Estructura de Carpetas
- **Windows:**
  ```bash
  mkdir C:\oracle-ai\oracle-ai-data-platform
  ```
- **macOS:**
  ```bash
  mkdir -p ~/oracle-ai/oracle-ai-data-platform
  ```
- Copie el contenido del repositorio clonado a esta carpeta.

### 3. Configurar el Wallet de Autonomous Database
- Descargue el Wallet desde la consola de OCI.

<p align="left">
  <img src="img/wallet.gif">
</p>

- Coloque el archivo en:
  ```plaintext
  oracle-ai-data-platform/app/wallet
  ```

### 4. Generar API Key y Configurar la Carpeta .oci
#### a) Generar la API Key

- En OCI, agregue la clave `key.pem` en **User Settings -> API Keys**.

<p align="left">
  <img src="img/api-key.gif">
</p>

#### b) Crear el Archivo de Configuración en `.oci`
- **Windows:**
  ```bash
  mkdir C:\Users\<su_usuario>\.oci
  ```
- **macOS:**
  ```bash
  mkdir ~/.oci
  ```
- Cree el archivo `config` en `.oci` con:
  ```plaintext
  [DEFAULT]
  user=<user_ocid>
  fingerprint=<fingerprint>
  key_file=~/.oci/key.pem
  tenancy=<tenancy_ocid>
  region=<region>
  ```

Cuando usas el archivo de configuración (config) de OCI, el parámetro region define la región predeterminada para tus operaciones. Para acceder a un bucket en Object Storage, debes asegurarte de estar apuntando a la misma región donde se encuentra ese bucket. Si tu config especifica, por ejemplo, region = `us-ashburn-1`, pero tu bucket está creado en `us-phoenix-1`, tendrás que:

- Cambiar la región en el archivo config a `us-phoenix-1`, o
- Crear un perfil adicional en ese mismo archivo con la región correcta, o
- Sobrescribir la región a través de un parámetro/flag en la CLI o variable de entorno cuando ejecutes los comandos.

En otras palabras, el valor de region en el config determina a qué región se dirigirán tus comandos por defecto. Si tu bucket está en otra región, no podrás manejarlo usando el perfil que apunte a la región equivocada; deberás indicar la región correcta de alguna de las formas mencionadas.

### 5. Configurar Variables de Entorno
Edite el archivo `.env` ubicado en `oracle-ai-data-platform/app/.env` y agregue los valores necesarios.

### 6. Instalar Dependencias y Ejecutar el Proyecto
Ejecute:
```bash
cd oracle-ai-data-platform
cd setup
python setup.py
```

### 7. Ejecion Manual
#### **Windows:**
```bash
cd oracle-ai-data-platform
cd app
conda activate oracle-ai
streamlit run app.py --server.port 8501
```

#### **macOS:**
```bash
cd app
source activate oracle-ai
streamlit run app.py --server.port 8501
```

## Data Model Documentation

Este modelo de datos está diseñado para una plataforma de análisis documental asistida por inteligencia artificial. Su objetivo es permitir a usuarios gestionar archivos, módulos funcionales, agentes de IA y análisis vectorial sobre fragmentos de documentos. Ofrece mecanismos de control de acceso, soporte para múltiples módulos AI y registro de metadatos enriquecidos.

<p align="center">
  <img src="img/data-model.svg">
</p>

https://www.mermaidchart.com/app/projects/a5976d52-778a-4839-b538-94feed349ce9/diagrams/37f8ba3f-ce9d-4f27-80d8-52fe5154713b/version/v0.1/edit

### Descripción de Tablas y Contenido Inicial

#### 1. `USER_GROUP`
Agrupa a los usuarios según su rol, organización o permisos. Cada grupo puede tener múltiples usuarios.

| Campo                   | Tipo            | Descripción                                 |
|-------------------------|-----------------|---------------------------------------------|
| `user_group_id`         | NUMBER (PK)     | Identificador único del grupo               |
| `user_group_name`       | VARCHAR2(250)   | Nombre del grupo                            |
| `user_group_description`| VARCHAR2(500)   | Descripción textual                         |
| `user_group_state`      | NUMBER          | Estado del grupo (1 = activo)               |
| `user_group_date`       | TIMESTAMP       | Fecha de creación                           |

#### 2. `USERS`
Usuarios registrados en la plataforma. Cada usuario está vinculado a un grupo.

| Campo                  | Tipo             | Descripción                                 |
|------------------------|------------------|---------------------------------------------|
| `user_id`              | NUMBER (PK)      | Identificador único del usuario             |
| `user_group_id`        | NUMBER (FK)      | Clave foránea a `user_group`                |
| `user_username`        | VARCHAR2(250)    | Nombre de usuario único                     |
| `user_password`        | VARCHAR2(500)    | Contraseña de ingreso                       |
| `user_sel_ai_password` | VARCHAR2(500)    | Contraseña para servicios AI                |
| `user_name`            | VARCHAR2(500)    | Nombre del usuario                          |
| `user_last_name`       | VARCHAR2(500)    | Apellido del usuario                        |
| `user_email`           | VARCHAR2(500)    | Correo electrónico                          |
| `user_modules`         | CLOB (JSON)      | Lista de módulos asignados (formato JSON)   |
| `user_state`           | NUMBER           | Estado del usuario (1 = activo)             |
| `user_date`            | TIMESTAMP        | Fecha de registro

**Contenido inicial:**

```sql
INSERT INTO users (
    user_id, user_group_id, user_username, user_password, user_sel_ai_password,
    user_name, user_last_name, user_email, user_modules
) VALUES (
    0, 0, 'admin', 'admin', 'p_a_s_s_w_o_r_d',
    'Joel', 'Ganggini', 'joel.ganggini@correo.com', '[0, 1, 2, 3, 4, 5, 6]'
);
```

#### 3. `MODULES`
Define los módulos funcionales que ofrece el sistema para el procesamiento de datos (p. ej. extracción de texto, RAG, OCR, etc).

| Campo                  | Tipo             | Descripción                                    |
|------------------------|------------------|------------------------------------------------|
| `module_id`            | NUMBER (PK)      | Identificador único del módulo                 |
| `module_name`          | VARCHAR2(250)    | Nombre del módulo                              |
| `module_folder`        | VARCHAR2(250)    | Carpeta asociada al módulo (backend/frontend)  |
| `module_src_type`      | VARCHAR2(250)    | Tipos de archivo de entrada (CSV, PDF, etc.)   |
| `module_trg_type`      | VARCHAR2(250)    | Tipos de archivo de salida (TXT, JSON, etc.)   |
| `module_vector_store`  | NUMBER           | Soporte para embeddings (1 = sí)               |
| `module_state`         | NUMBER           | Estado (1 = activo)                            |
| `module_date`          | TIMESTAMP        | Fecha de registro                              |

**Contenido inicial:**

```sql
INSERT INTO modules (module_id, module_name) VALUES (0, 'Administrator');
INSERT INTO modules (...) VALUES (1, 'Select AI', 'module-select-ai', 'CSV', 'Autonomous Database');
INSERT INTO modules (...) VALUES (2, 'Select AI RAG', 'module-select-ai-rag', 'TXT, HTML, DOC, JSON, XML', 'Autonomous Database');
INSERT INTO modules (...) VALUES (3, 'AI Document Understanding', 'module-ai-document-understanding', 'PDF, JPG, PNG, TIFF', 'PDF, JSON', 1);
INSERT INTO modules (...) VALUES (4, 'AI Speech to Text', 'module-ai-speech-to-text', 'M4A, MKV, MP3, MP4, OGA, OGG, WAV', 'TXT, SRT', 1);
INSERT INTO modules (...) VALUES (5, 'AI Document Multimodal', 'module-ai-document-multimodal', 'JPEG, PNG', 'MD', 1);
INSERT INTO modules (...) VALUES (6, 'AI Speech to Text Real-Time', 'module-ai-speech-to-realtime', 'JSON', 'TXT', 1);
```

#### 4. `AGENT_MODELS`
Modelos de IA configurables para los agentes (LLM, VLM, etc.).

| Campo                         | Tipo             | Descripción                                   |
|-------------------------------|------------------|-----------------------------------------------|
| `agent_model_id`              | NUMBER (PK)      | Identificador único del modelo                |
| `agent_model_name`            | VARCHAR2(250)    | Nombre del modelo (identificador externo)     |
| `agent_model_type`            | VARCHAR2(100)    | Tipo (`llm`, `vlm`)                           |
| `agent_model_provider`        | VARCHAR2(250)    | Proveedor del modelo (meta, cohere, etc.)     |
| `agent_model_service_endpoint`| VARCHAR2(500)    | Endpoint (placeholder por defecto)            |
| `agent_model_state`           | NUMBER           | Estado (1 = activo)                           |
| `agent_model_date`            | TIMESTAMP        | Fecha de registro                             |

**Contenido inicial:** 11 modelos entre `cohere`, `meta`, `xai`.

#### 5. `AGENTS`
Agentes configurados que usan un modelo para ejecutar tareas de QA, OCR, PII, etc.

| Campo                      | Tipo             | Descripción                                   |
|----------------------------|------------------|-----------------------------------------------|
| `agent_id`                 | NUMBER (PK)      | Identificador único del agente                |
| `agent_model_id`           | NUMBER (FK)      | Referencia a modelo en `agent_models`         |
| `agent_name`               | VARCHAR2(250)    | Nombre del agente                             |
| `agent_description`        | VARCHAR2(4000)   | Descripción de la funcionalidad               |
| `agent_type`               | VARCHAR2(250)    | Tipo (`Chat`, `Extraction`, etc.)             |
| `agent_max_out_tokens`     | NUMBER           | Máx. de tokens generados                      |
| `agent_temperature`        | NUMBER (1,1)     | Parámetro de diversidad                       |
| `agent_top_p`              | NUMBER (3,2)     | Nucleus sampling                              |
| `agent_top_k`              | NUMBER (3,0)     | Top-K sampling                                |
| `agent_frequency_penalty`  | NUMBER (3,2)     | Penalización por frecuencia                   |
| `agent_presence_penalty`   | NUMBER (3,2)     | Penalización por presencia                    |
| `agent_prompt_system`      | VARCHAR2(4000)   | Prompt del sistema                            |
| `agent_prompt_message`     | VARCHAR2(4000)   | Mensaje inicial opcional                      |
| `agent_state`              | NUMBER           | Estado del agente                             |
| `agent_date`               | TIMESTAMP        | Fecha de creación                             |

**Contenido inicial:** 5 agentes:
- Document Agent
- SRT Audio Agent
- PII Anonymizer Agent
- Image Analysis Agent
- Image OCR Analysis Agent

#### 6. `AGENT_USER`
Relación entre usuarios y agentes, incluyendo propiedad.

| Campo             | Tipo             | Descripción                             |
|-------------------|------------------|-----------------------------------------|
| `agent_user_id`   | NUMBER (PK)      | Identificador único de relación         |
| `agent_id`        | NUMBER (FK)      | Agente compartido o propio              |
| `user_id`         | NUMBER (FK)      | Usuario propietario o colaborador       |
| `owner`           | NUMBER           | 1 = Propietario, 0 = Compartido         |
| `agent_user_state`| NUMBER           | Estado de relación                      |
| `agent_user_date` | TIMESTAMP        | Fecha de asignación                     |

**Contenido inicial:** Admin (`user_id = 0`) posee los 5 agentes.

#### 7. `FILES`
Archivos subidos para análisis en los módulos.

| Campo                    | Tipo             | Descripción                              |
|--------------------------|------------------|------------------------------------------|
| `file_id`                | NUMBER (PK)      | Identificador único del archivo          |
| `module_id`              | NUMBER (FK)      | Módulo donde se subió el archivo         |
| `file_src_file_name`     | VARCHAR2(500)    | Nombre original del archivo              |
| `file_src_size`          | NUMBER           | Tamaño en bytes                          |
| `file_src_strategy`      | VARCHAR2(500)    | Estrategia de extracción aplicada        |
| `file_trg_obj_name`      | VARCHAR2(4000)   | Nombre del objeto generado               |
| `file_trg_extraction`    | CLOB             | Contenido extraído                       |
| `file_trg_tot_pages`     | NUMBER           | Páginas totales (si aplica)              |
| `file_trg_tot_characters`| NUMBER           | Total de caracteres extraídos            |
| `file_trg_tot_time`      | VARCHAR2(8)      | Tiempo total de audio (hh:mm:ss)         |
| `file_trg_language`      | VARCHAR2(3)      | Idioma (`esa`, `en`, etc.)               |
| `file_trg_pii`           | NUMBER           | Indicador si contiene PII                |
| `file_description`       | VARCHAR2(500)    | Descripción manual                       |
| `file_version`           | NUMBER           | Versión del archivo                      |
| `file_state`             | NUMBER           | Estado (1 = activo)                      |
| `file_date`              | TIMESTAMP        | Fecha de carga                           |


#### 8. `FILE_USER`
Relación entre usuarios y archivos, con control de propiedad y acceso.

| Campo            | Tipo             | Descripción                             |
|------------------|------------------|-----------------------------------------|
| `file_user_id`   | NUMBER (PK)      | ID único de relación                    |
| `file_id`        | NUMBER (FK)      | Archivo referenciado                    |
| `user_id`        | NUMBER (FK)      | Usuario que accede o es dueño           |
| `owner`          | NUMBER           | 1 = Propietario                         |
| `file_user_state`| NUMBER           | Estado de acceso                        |
| `file_user_date` | TIMESTAMP        | Fecha de asignación                     |

#### 9. `DOCS`
Fragmentos extraídos de archivos que se transforman en vectores semánticos.

| Campo      | Tipo         | Descripción                                 |
|------------|--------------|---------------------------------------------|
| `id`       | NUMBER (PK)  | ID único del fragmento                      |
| `file_id`  | NUMBER (FK)  | Archivo al que pertenece                    |
| `text`     | CLOB         | Texto del fragmento                        |
| `metadata` | CLOB         | Información adicional                      |
| `embedding`| VECTOR       | Embedding vectorial para búsqueda semántica |

- Índice: `docs_hnsw_idx` (similaridad coseno con precisión 95%)
- Trigger y secuencia de auto-incremento activados

### Relaciones Clave

| Relación                         | Tipo     | Descripción                                        |
|----------------------------------|----------|----------------------------------------------------|
| `USER_GROUP` ⟶ `USERS`          | 1:N      | Un grupo contiene varios usuarios.                 |
| `AGENT_MODELS` ⟶ `AGENTS`       | 1:N      | Un modelo puede ser usado por muchos agentes.      |
| `USERS` ⟷ `AGENTS`              | N:M      | Mediante `AGENT_USER`.                             |
| `USERS` ⟷ `FILES`               | N:M      | Mediante `FILE_USER`.                              |
| `MODULES` ⟶ `FILES`             | 1:N      | Un módulo genera múltiples archivos.               |
| `FILES` ⟶ `DOCS`                | 1:N      | Un archivo puede tener múltiples fragmentos.       |

---

## Consideraciones Adicionales

- Las relaciones `*_USER` (`AGENT_USER`, `FILE_USER`) permiten control granular de permisos, incluyendo el campo `OWNER`.
- `user_modules` permite flexibilidad al almacenar asignaciones como JSON en vez de una relación tradicional.
- `DOCS.embedding` es un campo tipo `VECTOR`, lo que indica que este modelo soporta búsquedas semánticas o recuperación basada en similitud.


## Referencias de Desarrollo con Python y Oracle

- [Connecting to Oracle Database](https://python-oracledb.readthedocs.io/en/latest/user_guide/connection_handling.html)  
  Guía oficial para conectar aplicaciones Python a Oracle Database usando `oracledb`.

- [OCI Python SDK - Ejemplos](https://github.com/oracle/oci-python-sdk/tree/master/examples/database_tools)  
  Repositorio oficial con ejemplos del SDK de Oracle Cloud Infrastructure para Python.

- [ObjectStorageClient - API Reference](https://oracle-cloud-infrastructure-python-sdk.readthedocs.io/en/latest/api/object_storage/client/oci.object_storage.ObjectStorageClient.html)  
  Documentación del cliente de Object Storage del SDK de OCI.

- [OCI Realtime Speech Python SDK](https://github.com/oracle/oci-ai-speech-realtime-python-sdk)  
  SDK oficial para transcripción de voz en tiempo real con OCI Speech.

- [LangChain + OCI Generative AI](https://python.langchain.com/docs/integrations/text_embedding/oci_generative_ai/)  
  Integración de LangChain con los modelos generativos de Oracle para embeddings de texto.

---

<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[issues-shield]: https://img.shields.io/github/issues/othneildrew/Best-README-Template.svg?style=for-the-badge
[issues-url]: https://github.com/jganggini/oci-functions/issues
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: https://www.linkedin.com/in/jganggini/