import pdfplumber
import re
from decimal import Decimal

def extraer_total_de_factura(ruta_pdf: str) -> Decimal | None:
    """
    Abre un archivo PDF, busca el total de la factura y lo devuelve como un valor numérico.

    Args:
        ruta_pdf: La ruta al archivo PDF de la factura.

    Returns:
        Un objeto Decimal con el total encontrado, o None si no se encuentra.
    """
    total_encontrado = None
    # Expresión regular para encontrar montos. Busca números con separadores de miles
    # (punto o coma) y un separador decimal (coma o punto).
    # Soporta opcionalmente símbolos de moneda al principio.
    patron_monto = re.compile(r"[\$\€]?\s*(\d{1,3}(?:[.,]\d{3})*[,.]\d{2})")

    try:
        with pdfplumber.open(ruta_pdf) as pdf:
            # Iteramos por las páginas, usualmente el total está en la última
            for pagina in reversed(pdf.pages):
                texto = pagina.extract_text()
                
                # Iteramos por cada línea de la página
                for linea in texto.split('\n'):
                    #print(f"🔍 Analizando línea: {linea.strip()}")
                    # Buscamos líneas que probablemente contengan el total
                    if 'TOTAL' in linea:
                        busqueda = patron_monto.search(linea)
                        if busqueda:
                            # Limpiamos el string del monto encontrado
                            monto_str = busqueda.group(1)
                            # Quitamos separadores de miles (puntos o comas)
                            monto_limpio = monto_str.replace('.', '').replace(',', '')
                            # Reemplazamos el último caracter por un punto decimal
                            monto_decimal_str = monto_limpio[:-2] + '.' + monto_limpio[-2:]
                            
                            total_encontrado = Decimal(monto_decimal_str)
                            #print(f"✅ Total encontrado en la línea '{linea.strip()}': {total_encontrado}")
                            return total_encontrado # Devolvemos el primer total encontrado

    except FileNotFoundError:
        print(f"❌ Error: El archivo no fue encontrado en la ruta: {ruta_pdf}")
        return None
    except Exception as e:
        print(f"❌ Ocurrió un error al procesar el PDF: {e}")
        return None

    print("🟡 No se pudo encontrar un valor total en el PDF.")
    return None