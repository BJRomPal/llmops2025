import streamlit as st
import pandas as pd
from google.cloud import storage
import io
import json 
import altair as alt # <--- ¡ESTO ES LO QUE FALTABA!

# ----------------- CONFIGURACIÓN DEL PROYECTO -----------------
# ¡IMPORTANTE! Reemplaza este valor con el nombre exacto de tu bucket
BUCKET_NAME = "tp_final_nube" 
FILE_NAME = "prueba.json" 
# --------------------------------------------------------------

# Inicializar df_invoices en el estado de sesión para mantener los datos
if 'df_invoices' not in st.session_state:
    st.session_state.df_invoices = pd.DataFrame()

# --------------------------------------------------------------
def load_data_from_gcs():
    """Descarga el JSON de GCS, lo decodifica, lo valida y lo carga en un DataFrame."""
    # ... (código de carga de datos sin cambios, es robusto)
    print("cargando JSON")
    try:
        client = storage.Client()
        bucket = client.bucket(BUCKET_NAME)
        blob = bucket.blob(FILE_NAME) 
        data_bytes = blob.download_as_bytes()
        data_string = data_bytes.decode('utf-8') 
        
        try:
            json_data = json.loads(data_string) 
            print("El archivo JSON es válido.")
        except json.JSONDecodeError as e:
            st.error("Error de Formato JSON: El archivo 'test.json' en GCS no es JSON válido.")
            st.code(f"Detalle del error de decodificación JSON: {e}")
            return pd.DataFrame() 

        df = pd.read_json(io.StringIO(data_string)) 
        return df
    
    except Exception as e:
        st.error(f"Error al cargar datos desde Cloud Storage. Verifica el nombre del bucket ({BUCKET_NAME}) y los permisos.")
        st.code(f"Detalle del error de GCS: {e}")
        return pd.DataFrame() 
# --------------------------------------------------------------

# --- INTERFAZ STREAMLIT ---
st.set_page_config(layout="wide")
st.title("PROYECTO_1: Facturación 202511 desde Cloud Storage")

# Botón para cargar/recargar los datos
if st.button('Cargar Datos JSON'):
    with st.spinner('Leyendo JSON desde Cloud Storage...'):
        # Almacenar los datos cargados en el estado de sesión
        st.session_state.df_invoices = load_data_from_gcs()
        
    if not st.session_state.df_invoices.empty:
        st.success(f"Datos cargados exitosamente. Se muestran {len(st.session_state.df_invoices)} registros.")
        
# Muestra la tabla si hay datos cargados
if not st.session_state.df_invoices.empty:
    st.dataframe(st.session_state.df_invoices)

    # ----------------------------------------------------------------------
    # GRÁFICO (AHORA DENTRO DE UN BLOQUE CONDICIONAL)
    # ----------------------------------------------------------------------

    # 1. Agrupar los datos por main_category y sumar la tarifa
    df_grouped = st.session_state.df_invoices.groupby('main_category')['tarifa'].sum().reset_index()

    # 2. Crear el gráfico de barras con Altair
    st.subheader("Tarifa Total por Categoría Principal")

    chart = alt.Chart(df_grouped).mark_bar().encode(
        x=alt.X('main_category', title='Categoría Principal'), 
        y=alt.Y('tarifa', title='Suma de Tarifa', axis=alt.Axis(format='$,f')), 
        color='main_category', 
        tooltip=['main_category', alt.Tooltip('tarifa', title='Tarifa Total', format='$,f')]
    ).properties(
        title='Distribución de la Tarifa por Main Category'
    ).interactive() 

    # 3. Mostrar el gráfico en Streamlit
    st.altair_chart(chart, use_container_width=True)

# Mensaje de advertencia si no hay datos
else:
    st.warning("No se pudieron cargar los datos o no se ha presionado el botón 'Cargar Datos JSON'.")