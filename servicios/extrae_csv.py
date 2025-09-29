import pandas as pd

def extrae_csv(ruta_csv):
    """
    Lee un archivo CSV y devuelve su contenido como un DataFrame de pandas.

    Args:
        ruta_csv: La ruta al archivo CSV.

    Returns:
        Un DataFrame con los datos del CSV.
        El periodo extraído del CSV.
    """
    try:
        df = pd.read_csv(ruta_csv)
        periodo = df['periodo'].unique()[0]
        return df, periodo
    except FileNotFoundError:
        print(f"❌ Error: El archivo no fue encontrado en la ruta: {ruta_csv}")
        return None
    except Exception as e:
        print(f"❌ Ocurrió un error al procesar el CSV: {e}")
        return None