import streamlit as st
import pandas as pd
from google.cloud import storage
import io
import json 
import altair as alt # <--- ¡ESTO ES LO QUE FALTABA!
from servicios import extrae_csv, extrae_pdf, compara_totales
import tempfile
import os


# --- TUS FUNCIONES DE CHEQUEO (EJEMPLOS) ---
# Deberás reemplazar estas con tus funciones reales.

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(layout="wide")


# ======================================================================
# BARRA LATERAL (SIDEBAR)
# ======================================================================
with st.sidebar:
    st.header("Carga de Archivos para Chequeo")

    pdf_file = st.file_uploader("Sube tu factura PDF", type="pdf")
    csv_file = st.file_uploader("Sube tu reporte CSV", type="csv")

    if st.button("Chequear Totales"):
        if pdf_file and csv_file:
            with st.spinner("Procesando archivos..."):
                # Crear un archivo temporal para el PDF
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
                    tmp_pdf.write(pdf_file.getvalue())
                    pdf_path = tmp_pdf.name

                # Crear un archivo temporal para el CSV
                with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp_csv:
                    tmp_csv.write(csv_file.getvalue())
                    csv_path = tmp_csv.name

                st.info("Archivos temporales creados. Pasando rutas a las funciones...")

                # Pasar las RUTAS de los archivos temporales a tus funciones
                total_factura_pdf = extrae_pdf.extraer_total_de_factura(pdf_path)
                total_reporte_csv = extrae_csv.extrae_csv(csv_path)
                total = compara_totales.compara_totales(total_factura_pdf, total_reporte_csv)

                # Limpiar los archivos temporales explícitamente después de usarlos
                #os.remove(pdf_path)
                #os.remove(csv_path)

                # Mostrar los resultados
                if total:
                    st.success("Los totales conciden perfectamente.")
                else:
                    st.error(f"No coinciden los totales entre Factura y soporte")
        else:
            st.warning("Por favor, asegúrate de subir ambos archivos.")
