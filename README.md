# Sistema Inteligente de Auditoría de Facturas y Dimensiones

Una aplicación web para validar automáticamente los totales de las facturas de envío contra sus CSV de respaldo y verificar las dimensiones de los productos utilizando IA, registrando las discrepancias en una base de datos en la nube.

## Descripción General 🧾

En la logística, es común que las facturas de envío contengan errores, ya sea en el total facturado o en las dimensiones y pesos de los paquetes (peso aforado), lo que genera sobrecostos. Este proyecto automatiza el proceso de auditoría.

La aplicación permite a un usuario cargar un archivo de factura y su CSV correspondiente. El sistema realiza dos validaciones clave:

1.  **Validación de Totales:** Compara el total monetario de la factura con la suma de las tarifas en el archivo CSV.
2.  **Validación de Dimensiones:** Para cada producto en el CSV, utiliza la API de Tavily para buscar en la web y la API de Gemini para extraer las dimensiones y peso reales del producto. Luego, compara estos datos con los informados en el CSV.

Todas las discrepancias encontradas se registran en una tabla `scales` en una base de datos Google Cloud SQL, creando un registro auditable. La interfaz está construida con Streamlit y está diseñada para ser desplegada en Google Cloud Run.

## 🚀 Features

* **Interfaz Interactiva:** Carga de archivos de factura y CSV directamente desde el navegador.
* **Auditoría de Totales:** Verificación automática del total de la factura contra los datos del CSV.
* **Verificación con IA:** Búsqueda web inteligente para encontrar dimensiones y pesos de productos.
* **Cálculo de Discrepancias:** Identifica y calcula las diferencias entre los datos informados y los datos reales.
* **Registro en Base de Datos:** Almacena de forma persistente todas las discrepancias encontradas en Cloud SQL.
* **Escalable y Serverless:** Desplegado en Cloud Run para una gestión sin servidores y escalado automático.

## 🛠️ Arquitectura y Tech Stack

El proyecto utiliza una arquitectura moderna serverless para procesar los datos de manera eficiente.

* **Frontend:** Streamlit
* **Backend & Lógica:** Python
* **Base de Datos:** Google Cloud SQL (MySQL)
* **Búsqueda Web:** Tavily API
* **Extracción de Datos (IA):** Google Gemini API (Vertex AI)
* **Hosting:** Google Cloud Run
* **Almacenamiento de Archivos:** Google Cloud Storage
* **Contenerización:** Docker
* **Flujo de Datos:** Usuario → Streamlit UI (Cloud Run) → Backend Python → (Tavily/Gemini APIs) & (Cloud SQL / Cloud Storage)

## 🗄️ Esquema de la Base de Datos

La base de datos contiene principalmente tres tablas:

* **`invoices`**: Almacena la información de cada envío o línea del CSV.
* **`tarifario`**: Contiene las reglas de precios y tarifas.
* **`scales`**: Registra los resultados de la verificación de dimensiones. Cada fila tiene una `ForeignKey` al `id` de la tabla `invoices`, vinculando la discrepancia con el envío específico.

---

## ⚙️ Ejecución en Entorno Local

Para ejecutar la aplicación en tu máquina mientras te conectas a los servicios de Google Cloud, sigue estos pasos:

1.  **Clonar el Repositorio**
    ```bash
    git clone [https://github.com/BJRomPal/llmops2025.git](https://github.com/BJRomPal/llmops2025.git)
    cd llmops2025
    ```

2.  **Configurar Entorno Virtual y Dependencias**
    ```bash
    python -m venv venv
    source venv/bin/activate  # En Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```

3.  **Configurar Google Cloud Platform (GCP)**
    * Crea un nuevo proyecto en la [Consola de GCP](https://console.cloud.google.com/).
    * Habilita las APIs necesarias: **Cloud SQL Admin API**, **Vertex AI API**, y **Cloud Storage API**.
    * **Cloud SQL:** Crea una instancia de MySQL y una base de datos. Anota el **nombre de conexión de la instancia**, crea un **usuario** y una **contraseña**.
    * **Cloud Storage:** Crea un bucket. Anota el **nombre del bucket**.
    * **Permisos:** Asegúrate de que tu cuenta de usuario en IAM tenga los roles necesarios para administrar estos servicios (ej. `Editor` o roles específicos como `Administrador de Cloud SQL`, `Administrador de Storage`).

4.  **Generar Claves de API**
    * **Gemini API:** Genera tu clave de API desde la consola de Vertex AI o Google AI Studio.
    * **Tavily API:** Obtén tu clave de API desde el [sitio web de Tavily](https://tavily.com/).

5.  **Crear el archivo `.env`**
    En la raíz del proyecto, crea un archivo llamado `.env` y llénalo con tus credenciales. Usa el siguiente formato:
    ```env
    GOOGLE_CLOUD_PROJECT="tu-id-de-proyecto-gcp"
    DB_USER="tu-usuario-de-base-de-datos"
    DB_PASSWORD="tu-contraseña-de-base-de-datos"
    DB_NAME="el-nombre-de-tu-base-de-datos"
    INSTANCE_CONNECTION_NAME="proyecto:region:instancia"
    BUCKET_NAME="el-nombre-de-tu-bucket"
    GOOGLE_API_KEY="tu-api-key-de-gemini"
    TAVILY_API_KEY="tu-api-key-de-tavily"
    ```

6.  **Autenticar tu Máquina Local**
    Para que tu aplicación local pueda acceder a los servicios de GCP (Cloud SQL, Cloud Storage), autentica tu SDK de `gcloud`:
    ```bash
    gcloud auth application-default login
    ```
    Este comando abrirá un navegador para que inicies sesión con tu cuenta de Google. Tu cuenta debe tener permisos de **Cliente de Cloud SQL** y **Administrador de objetos de Storage**.

7.  **Ejecutar la Aplicación**
    ¡Ya está todo listo! Inicia la aplicación Streamlit:
    ```bash
    streamlit run app.py
    ```

---

## ☁️ Despliegue en Google Cloud Run

Este es el proceso para empaquetar la aplicación en un contenedor y desplegarla como un servicio serverless.

1.  **Habilitar APIs en GCP**
    Asegúrate de que las siguientes APIs estén habilitadas en tu proyecto: **Cloud Run API**, **Artifact Registry API**, **Secret Manager API** y **Cloud Build API**.

2.  **Guardar Secretos en Secret Manager**
    Por seguridad, nunca expongas tus credenciales directamente. Guárdalas en Secret Manager:
    * `GOOGLE_API_KEY`
    * `TAVILY_API_KEY`
    * `DB_USER`
    * `DB_PASSWORD`
    * Crea un secreto para cada una de estas claves. Por ejemplo:
        ```bash
        printf "tu-contraseña-de-base-de-datos" | gcloud secrets versions add llmops-db-password --data-file=-
        ```

3.  **Construir y Subir la Imagen de Docker**
    * **Crear Repositorio:** Primero, crea un repositorio en Artifact Registry para almacenar tu imagen.
        ```bash
        gcloud artifacts repositories create llmops2025 --repository-format=docker --location=us-central1
        ```
    * **Autenticar Docker:** Configura Docker para que pueda conectarse a Artifact Registry.
        ```bash
        gcloud auth configure-docker us-central1-docker.pkg.dev
        ```
    * **Construir la Imagen:** Desde la raíz de tu proyecto (donde está el `Dockerfile`), ejecuta:
        ```bash
        docker build -t us-central1-docker.pkg.dev/tu-id-de-proyecto-gcp/llmops2025/analizador-facturas .
        ```
    * **Subir la Imagen:**
        ```bash
        docker push us-central1-docker.pkg.dev/tu-id-de-proyecto-gcp/llmops2025/analizador-facturas
        ```

4.  **Desplegar el Servicio en Cloud Run**
    Ejecuta el siguiente comando para desplegar tu aplicación. Este comando conecta el servicio a Cloud SQL, inyecta las variables de configuración y los secretos, y asigna los permisos necesarios.

    * **Permisos:** Antes de desplegar, asegúrate de que la **cuenta de servicio de Compute Engine por defecto** (`NUMERO-PROYECTO-compute@developer.gserviceaccount.com`) tenga los siguientes roles en IAM:
        * `Cliente de Cloud SQL`
        * `Accesor de secretos de Secret Manager`
        * `Administrador de objetos de Storage`

    * **Comando de Despliegue:**
        ```bash
        gcloud run deploy analizador-facturas \
            --image us-central1-docker.pkg.dev/tu-id-de-proyecto-gcp/llmops2025/analizador-facturas \
            --platform managed \
            --region us-central1 \
            --allow-unauthenticated \
            --set-env-vars="GOOGLE_CLOUD_PROJECT=tu-id-de-proyecto-gcp,DB_NAME=el-nombre-de-tu-base-de-datos,INSTANCE_CONNECTION_NAME=proyecto:region:instancia,BUCKET_NAME=el-nombre-de-tu-bucket" \
            --set-secrets="GOOGLE_API_KEY=llmops-google-api-key:latest,TAVILY_API_KEY=llmops-tavily-api-key:latest,DB_USER=llmops-db-user:latest,DB_PASSWORD=llmops-db-password:latest"
        ```

    Una vez finalizado el despliegue, `gcloud` te proporcionará la URL pública de tu aplicación.
