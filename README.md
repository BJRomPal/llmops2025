# Sistema Inteligente de Auditoría de Facturas y Dimensiones
Una aplicación web para validar automáticamente los totales de las facturas de envío contra sus CSV de respaldo y verificar las dimensiones de los productos utilizando IA, registrando las discrepancias en una base de datos en la nube.

## Descripción General 🧾
En la logística, es común que las facturas de envío contengan errores, ya sea en el total facturado o en las dimensiones y pesos de los paquetes (peso aforado), lo que genera sobrecostos. Este proyecto automatiza el proceso de auditoría.

La aplicación permite a un usuario cargar un archivo de factura y su CSV correspondiente. El sistema realiza dos validaciones clave:

Validación de Totales: Compara el total monetario de la factura con la suma de las tarifas en el archivo CSV.

Validación de Dimensiones: Para cada producto en el CSV, utiliza la API de Tavily para buscar en la web y la API de Gemini para extraer las dimensiones y peso reales del producto. Luego, compara estos datos con los informados en el CSV.

Todas las discrepancias encontradas se registran en una tabla scales en una base de datos Google Cloud SQL, creando un registro auditable. La interfaz está construida con Streamlit y está diseñada para ser desplegada en Google Cloud Run.

## 🚀 Features
Interfaz Interactiva: Carga de archivos de factura y CSV directamente desde el navegador.

Auditoría de Totales: Verificación automática del total de la factura contra los datos del CSV.

Verificación con IA: Búsqueda web inteligente para encontrar dimensiones y pesos de productos.

Cálculo de Discrepancias: Identifica y calcula las diferencias entre los datos informados y los datos reales.

Registro en Base de Datos: Almacena de forma persistente todas las discrepancias encontradas en Cloud SQL.

Escalable y Serverless: Desplegado en Cloud Run para una gestión sin servidores y escalado automático.

## 🛠️ Arquitectura y Tech Stack
El proyecto utiliza una arquitectura moderna serverless para procesar los datos de manera eficiente.

- Frontend: Streamlit

- Backend & Lógica: Python

- Base de Datos: Google Cloud SQL (MySQL)

- Búsqueda Web: Tavily API

- Extracción de Datos (IA): Google Gemini API

- Hosting: Google Cloud Run

- Contenerización: Docker

Flujo de Datos:
Usuario → Streamlit UI (Cloud Run) → Backend Python → (Tavily/Gemini APIs) & (Cloud SQL)

## ⚙️ Configuración del Entorno Local
Para ejecutar este proyecto en tu máquina local, sigue estos pasos:

1. Prerrequisitos
Python 3.9+

Cuenta de Google Cloud con un proyecto configurado.

Claves de API para Google Gemini y Tavily.

## ☁️ Despliegue en Cloud Run
Para desplegar la aplicación en Cloud Run, necesitarás:

Un Dockerfile: Para empaquetar la aplicación Streamlit en una imagen de contenedor.

Configurar la Conexión a Cloud SQL: Asegúrate de que tu servicio de Cloud Run tenga los permisos y la configuración de red para conectarse a tu instancia de Cloud SQL.

Gestionar Secretos: Guarda tus claves de API y credenciales de la base de datos en Google Secret Manager y otórgale acceso a tu servicio de Cloud Run.

Desplegar el Servicio: Usa el comando gcloud run deploy para desplegar la imagen del contenedor desde Artifact Registry.

## 🗄️ Esquema de la Base de Datos
La base de datos contiene principalmente tres tablas:

invoices: Almacena la información de cada envío o línea del CSV.

tarifario: Contiene las reglas de precios y tarifas.

scales: Registra los resultados de la verificación de dimensiones. Cada fila tiene una ForeignKey al id de la tabla invoices, vinculando la discrepancia con el envío específico.