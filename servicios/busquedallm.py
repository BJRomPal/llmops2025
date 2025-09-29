import os
import pandas as pd
import json
import google.generativeai as genai
from servicios.pydantic_model import ProductDimensions
from dotenv import load_dotenv
from tavily import TavilyClient
from servicios.consulta_invoices import trae_invoices
from servicios.consulta_tarificacion import trae_tarifas

def realiza_busqueda_llm(periodo) -> pd.DataFrame:
    """Realiza una búsqueda avanzada usando Tavily y extrae dimensiones con Gemini."""

    load_dotenv()
    tavily_api_key = os.getenv("TAVILY_API_KEY")
    google_api_key = os.getenv("GOOGLE_API_KEY")

    df = trae_invoices(periodo)
    tarifas = trae_tarifas()
    tarifas['tarifa'] = tarifas['tarifa'].astype(float)
    tarifas['ambito'] = tarifas['ambito'].astype(int)
    df['tarifa'] = df['tarifa'].astype(float)

    productos = []
    for row in df.itertuples():
        print(f"\nProcesando producto: {row.name}")
        dimensiones = buscar_dimensiones_producto(row.name, tavily_api_key, google_api_key)
        if dimensiones:
            try:
                producto = ProductDimensions(**dimensiones)
                print(f"  - Dimensiones extraídas: {producto}")
                id = row.id
                ambito = row.ambito
                operacion = row.tipo_servicio
                alto_valor = producto.alto
                ancho_valor = producto.ancho
                largo_valor = producto.largo
                peso_valor = producto.peso
                tarifa_proveedor = row.tarifa
                try:
                    peso_aforado = ancho_valor * largo_valor * alto_valor / 4000 # Peso aforado en kg
                except Exception as e:
                    print(f"  - Error al calcular el peso aforado: {e}")
                    peso_aforado = 0
                try:    
                    peso_facturable = max(peso_valor, peso_aforado) # Peso facturable en kg
                except Exception as e:
                    print(f"  - Error al calcular el peso facturable: {e}")
                    peso_facturable = 0
                mask = (
                    (tarifas['ambito'] == ambito) & 
                    (tarifas['tipo_de_servicio'] == operacion) & 
                    (tarifas['rango_desde'] <= peso_facturable) & 
                    (tarifas['rango_hasta'] >= peso_facturable)
                )
                
                # Aplicar la máscara y seleccionar la columna 'tarifa'
                resultado_tarifa = tarifas.loc[mask, 'tarifa']

                # Extraer el valor numérico (si se encontró)
                if not resultado_tarifa.empty:
                    tarifa_real = resultado_tarifa.iloc[0]
                else:
                    tarifa_real = None # O 0, o np.nan, para manejar casos sin tarifa
                diferencia = tarifa_proveedor - tarifa_real if tarifa_real is not None else None

                #print(f"  - Tarifa encontrada: {tarifa_real}")
                datos = {
                    "invoice_id": id,
                    "nombre_producto": row.name,
                    "track_code": row.track_code,
                    "alto": alto_valor,
                    "ancho": ancho_valor,
                    "largo": largo_valor,
                    "peso_aforado": peso_aforado,
                    "peso_fisico": peso_valor,
                    "peso_facturable": peso_facturable,
                    "tarifa_proveedor": tarifa_proveedor,
                    "tarifa_real": tarifa_real,
                    "diferencia": diferencia,
                }
                if tarifa_real < tarifa_proveedor:
                    productos.append(datos)
                
            except Exception as e:
                print(f"  - Error al validar las dimensiones con Pydantic: {e}")
        else:
            print("  - No se pudieron extraer dimensiones para este producto.")
    return pd.DataFrame(productos)


def extraer_datos_con_gemini(contexto: str, nombre_producto: str, google_api_key) -> dict:
    """Usa Gemini para extraer las dimensiones del texto de búsqueda."""
    genai.configure(api_key=google_api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    prompt = f"""
    Basado en el siguiente contexto de búsqueda para el producto "{nombre_producto}", 
    extrae el alto, ancho, largo y peso.
    
    - Si encuentras las dimensiones exactas, úsalas.
    - Si no las encuentras, busca dimensiones de productos muy similares mencionados en el contexto.
    - Devuelve los valores como números flotantes (float).
    - Tu respuesta DEBE ser únicamente un objeto JSON con las claves "alto", "ancho", "largo", "peso".
    - En la clave "fuente" indica de que pagina web o fuente obtuviste la información.
    - Si no encuentras la fuente, pon "desconocida".
    - Si no puedes determinar alguno de los valores, intenta predecirlo basado en productos similares. determina que tipo de producto es y busca dimensiones típicas.
    - Selecciona la opción más representativa y confiable, utiliza las medidas que a veces suelen estar en el nombre de la publicación o en las imagenes. 
    - Sé especialmente ágil y eficiente al estimar medidas y **sobretodo** peso físico.

    Contexto:
    ---
    {contexto}
    ---
    """
    
    try:
        response = model.generate_content(prompt)
        # Limpiar la respuesta para asegurar que sea un JSON válido
        json_text = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(json_text)
    except (json.JSONDecodeError, Exception) as e:
        print(f"  - Error al procesar la respuesta de Gemini: {e}")
        return {}


def buscar_dimensiones_producto(nombre_producto: str, tavily_api_key, google_api_key) -> dict:
    """Usa Tavily para buscar y Gemini para extraer las dimensiones."""
    tavily_client = TavilyClient(api_key=tavily_api_key)
    print(f"\n🔎 Buscando con Tavily: '{nombre_producto}'...")
    
    try:
        # Búsqueda avanzada con Tavily
        search_context = tavily_client.search(
            query=f'dimensions (height, width, length, weight) for product "{nombre_producto}"',
            search_depth="advanced" # Búsqueda más profunda
        )
        
        # Combinamos los resultados para dárselos a Gemini
        contexto_combinado = "\n".join([str(res) for res in search_context['results']])
        
        if not contexto_combinado:
            print("  - Tavily no devolvió resultados.")
            return {}
            
        print("  - Resultados de Tavily obtenidos. Extrayendo con Gemini...")
        datos_extraidos = extraer_datos_con_gemini(contexto_combinado, nombre_producto, google_api_key)
        
        if datos_extraidos:
            print("  - ✅ ¡Extracción con Gemini exitosa!")
            datos_extraidos['fuente'] = "Tavily + Gemini"
            return datos_extraidos
        else:
            print("  - 🟡 Gemini no pudo extraer los datos del contexto.")
            return {}

    except Exception as e:
        print(f"  - ❌ Error durante la búsqueda con Tavily: {e}")
        return {}
    