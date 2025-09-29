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
from servicios.busquedallm import realiza_busqueda_llm
from servicios.db.database_operations import insert_scales_data

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
st.title("Dashboard de Análisis de Facturas 📄🔍")

# --- INICIALIZACIÓN DEL ESTADO DE SESIÓN ---
# 'analysis_ready': controla la visibilidad del botón de análisis.
if 'analysis_ready' not in st.session_state:
    st.session_state.analysis_ready = False
# 'df_results': almacenará el dataframe del análisis.
if 'df_results' not in st.session_state:
    st.session_state.df_results = None
# 'periodo': almacenará el periodo extraído del CSV.
if 'periodo' not in st.session_state:
    st.session_state.periodo = 0
# 'csv_download_data': almacenará los datos del CSV listos para descargar.
if 'csv_download_data' not in st.session_state:
    st.session_state.csv_download_data = None

# ======================================================================
# BARRA LATERAL (SIDEBAR)
# ======================================================================
with st.sidebar:
    st.header("Carga de Archivos para Chequeo")

    mensajes_sidebar = st.empty()

    pdf_file = st.file_uploader("Sube tu factura PDF", type="pdf")
    csv_file = st.file_uploader("Sube tu reporte CSV", type="csv")

    if st.button("Chequear Totales"):
        # Resetea el estado cada vez que se presiona el botón
        st.session_state.analysis_ready = False
        st.session_state.df_results = None
        st.session_state.periodo = 0
        st.session_state.csv_download_data = None # Limpiar datos de descarga
        
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
                total_reporte_csv, periodo = extrae_csv.extrae_csv(csv_path)
                st.session_state.periodo = periodo # Guardar periodo en el estado
                son_iguales = compara_totales.compara_totales(total_factura_pdf, total_reporte_csv)
                

                # --- LÓGICA CONDICIONAL ---
            if son_iguales:
                st.success("Los totales coinciden perfectamente. Procediendo con las cargas...")
                
                try:
                    # --- 1. Subir archivos a GCS ---
                    st.info("Subiendo archivos a Cloud Storage e insertando registros en SQL...")
                    pdf_blob_name = f"facturas/{pdf_file.name}"
                    csv_blob_name = f"csv/{csv_file.name}"
                    
                    pdf_uploaded = upload_to_gcs(bucket_name, pdf_file, pdf_blob_name)
                    csv_uploaded = upload_to_gcs(bucket_name, csv_file, csv_blob_name)
                    
                    if not (pdf_uploaded and csv_uploaded):
                        st.error("Falló la subida de archivos a GCS. Proceso abortado.")
                        
                    # --- 2. Cargar CSV a la base de datos ---
                    carga_csv.carga_invoices(csv_path)

                    # --- 3. Actualizar estado de la app ---
                    st.session_state.analysis_ready = True

                except Exception as e:
                    # Capturar cualquier error durante el proceso
                    st.error(f"Ocurrió un error: {e}")
                
                finally:
                    # --- 4. Limpiar archivos temporales ---
                    # Este bloque se ejecuta siempre, haya error o no.
                    if os.path.exists(pdf_path):
                        os.remove(pdf_path)
                    if os.path.exists(csv_path):
                        os.remove(csv_path)
                with mensajes_sidebar.container():
                    st.success("¡Archivos subidos y Datos cargados en la base de datos exitosamente!")
                    st.write("Limpieza de archivos temporales finalizada.")

            else:
                st.error("No coinciden los totales entre Factura y soporte.")
        else:
            st.warning("Por favor, asegúrate de subir ambos archivos.")

    # --- BOTÓN CONDICIONAL PARA INICIAR ANÁLISIS ---
    if st.session_state.analysis_ready:
        st.markdown("---") # Separador visual
        if st.button("🚀 Iniciar Análisis"):
            mensajes_sidebar.empty()
            with st.spinner("Realizando análisis con el modelo..."):
                # Llama a la función y guarda el resultado en el estado de sesión
                st.session_state.df_results = realiza_busqueda_llm(st.session_state.periodo)
                st.session_state.csv_download_data = None # Limpiar datos de descarga previos
                st.balloons()
                st.success("¡Análisis completado!")

# ======================================================================
# PÁGINA PRINCIPAL
# ======================================================================

@st.cache_data
def convert_df_to_csv(df):
    """Convierte un DataFrame a un string de bytes en formato CSV."""
    return df.to_csv(index=False).encode('utf-8')

# --- NUEVA SECCIÓN: Mostrar los resultados del análisis ---
# Esto se mostrará solo si el dataframe existe en el estado de sesión
if st.session_state.df_results is not None:
    st.subheader("Resultados del Análisis")
    
    # Columnas que quieres mostrar en la tabla
    columnas_a_mostrar = [
        'nombre_producto', 
        'track_code', 
        'peso_facturable', 
        'tarifa_proveedor', 
        'tarifa_real', 
        'diferencia'
    ]
    
    # Filtra el DataFrame para mostrar solo las columnas deseadas
    df_filtrado = st.session_state.df_results[columnas_a_mostrar]
    
    # Muestra el DataFrame en la página principal
    st.dataframe(df_filtrado)
    
    st.markdown("---")
    
# --- LÓGICA PARA EL BOTÓN DE DOBLE ACCIÓN ---

    # 1. Botón principal que inicia la acción
    if st.button("Guardar en BD y Generar Reporte"):
        with st.spinner("Procesando..."):
            insert_success = insert_scales_data(st.session_state.df_results)

            if insert_success:
                st.success("¡Datos guardados en la base de datos exitosamente!")
                # Prepara los datos del CSV para la descarga y los guarda en el estado
                st.session_state.csv_download_data = convert_df_to_csv(df_filtrado)
            else:
                st.error("Hubo un problema al guardar los datos en la base de datos.")
                st.session_state.csv_download_data = None

    # 2. El botón de descarga solo aparece si los datos del CSV están listos
    #    Usamos .get() para acceder de forma segura y evitar el KeyError.
    if st.session_state.get("csv_download_data") is not None:
        file_name = f"periodo_{st.session_state.periodo}.csv"
        st.download_button(
           label="📥 Descargar Reporte CSV",
           data=st.session_state.csv_download_data,
           file_name=file_name,
           mime='text/csv'
        )
else:
    st.info("Carga los archivos en la barra lateral y ejecuta el análisis para ver los resultados aquí.")