import streamlit as st
import pandas as pd
from google.cloud import storage
import io
import json 
import altair as alt
from servicios import extrae_csv, extrae_pdf, compara_totales, carga_csv
import tempfile
import os
import dotenv
import google.auth

dotenv.load_dotenv()

bucket_name = os.getenv('BUCKET_NAME')

# --- FUNCIÓN PARA SUBIR ARCHIVOS A GCS ---
# Debes configurar tus credenciales de GCP en el entorno donde ejecutes esto.
def upload_to_gcs(bucket_name, file_object, destination_blob_name):
    """Sube un objeto de archivo en memoria a un bucket de GCS."""
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)

        # Volver al inicio del archivo antes de subirlo
        file_object.seek(0)
        
        blob.upload_from_file(file_object)
        print(f"Archivo {destination_blob_name} subido exitosamente a {bucket_name}.")
        return True
    except Exception as e:
        print(f"Error al subir a GCS: {e}")
        return False

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(layout="wide")

# Inicializar el estado de sesión para el botón de análisis
if 'analysis_ready' not in st.session_state:
    st.session_state.analysis_ready = False

# ======================================================================
# BARRA LATERAL (SIDEBAR)
# ======================================================================
with st.sidebar:
    st.header("Carga de Archivos para Chequeo")

    pdf_file = st.file_uploader("Sube tu factura PDF", type="pdf")
    csv_file = st.file_uploader("Sube tu reporte CSV", type="csv")

    if st.button("Chequear Totales"):
        # Resetea el estado cada vez que se presiona el botón
        st.session_state.analysis_ready = False
        
        if pdf_file and csv_file:
            with st.spinner("Procesando archivos..."):
                # (Tu lógica de archivos temporales se mantiene igual)
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
                    tmp_pdf.write(pdf_file.getvalue())
                    pdf_path = tmp_pdf.name
                with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp_csv:
                    tmp_csv.write(csv_file.getvalue())
                    csv_path = tmp_csv.name

                total_factura_pdf = extrae_pdf.extraer_total_de_factura(pdf_path)
                total_reporte_csv = extrae_csv.extrae_csv(csv_path)
                son_iguales = compara_totales.compara_totales(total_factura_pdf, total_reporte_csv)
                

                # --- LÓGICA CONDICIONAL ---
            if son_iguales:
                st.success("Los totales coinciden perfectamente. Procediendo con las cargas...")
                
                try:
                    # --- 1. Subir archivos a GCS ---
                    st.info("Subiendo archivos a Cloud Storage...")
                    pdf_blob_name = f"facturas/{pdf_file.name}"
                    csv_blob_name = f"csv/{csv_file.name}"
                    
                    pdf_uploaded = upload_to_gcs(bucket_name, pdf_file, pdf_blob_name)
                    csv_uploaded = upload_to_gcs(bucket_name, csv_file, csv_blob_name)
                    
                    if not (pdf_uploaded and csv_uploaded):
                        st.error("Falló la subida de archivos a GCS. Proceso abortado.")
                        
                    st.success("¡Archivos subidos a GCS exitosamente!")

                    # --- 2. Cargar CSV a la base de datos ---
                    st.info("Cargando datos en Cloud SQL...")
                    carga_csv.carga_invoices(csv_path)
                    st.success("¡Datos cargados en la base de datos exitosamente!")

                    # --- 3. Actualizar estado de la app ---
                    st.session_state.analysis_ready = True

                except Exception as e:
                    # Capturar cualquier error durante el proceso
                    st.error(f"Ocurrió un error: {e}")
                
                finally:
                    # --- 4. Limpiar archivos temporales ---
                    # Este bloque se ejecuta siempre, haya error o no.
                    st.info("Limpiando archivos temporales...")
                    if os.path.exists(pdf_path):
                        os.remove(pdf_path)
                    if os.path.exists(csv_path):
                        os.remove(csv_path)
                    st.write("Limpieza finalizada.")

            else:
                st.error("No coinciden los totales entre Factura y soporte.")
        else:
            st.warning("Por favor, asegúrate de subir ambos archivos.")

    # --- BOTÓN CONDICIONAL PARA INICIAR ANÁLISIS ---
    # Este bloque solo se muestra si `analysis_ready` es True
    if st.session_state.analysis_ready:
        st.markdown("---") # Separador visual
        if st.button("🚀 Iniciar Análisis"):
            with st.spinner("Iniciando análisis... (esto podría activar un Cloud Function, etc.)"):
                # Aquí iría la lógica para iniciar tu análisis
                st.balloons()
                st.success("¡Análisis iniciado!")
                st.info("El proceso de análisis ha comenzado. Los resultados se mostrarán en el dashboard principal.")